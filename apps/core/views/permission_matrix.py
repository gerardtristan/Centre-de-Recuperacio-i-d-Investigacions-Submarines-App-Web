"""Administració: editor de permisos dels rols (T-RP-03; 059 i 060; RN-RP-03 a 11; CA-RP-03, 04,
05, 07, 09 i 10). Disseny: l'Avisador (T-DX-19, `design-system.md`, «Rols i permisos»).

- Només amb M3b (`core.permissions.edit`, protegit i exclusiu de l'administrador): la resta de
  rols, també el President, «no trobat».
- Tota la matriu és un sol formulari. «Mostra el resum» i «Torna a la configuració inicial» no
  desen res: tornen la matriu amb les cel·les que canvien marcades, el resum i els comptes
  afectats. «Desa» és un POST amb CSRF, la nota, la casella de revisió i un codi TOTP nou.
- Les condicions (versió de base, regles protegides, abasts i `requires`) es miren abans de
  demanar el codi, i el servei les torna a mirar dins la transacció.
- Una cel·la que no és editable (un permís protegit, un rol que no és de gestió) a la petició
  rebutja tot el canvi (CA-RP-09): la pantalla no en mostra cap control.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import OperationalError
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts.security import AREA_ADMIN, WRONG_CODE, confirm_code

from .. import permission_matrix as matrix
from ..permission_catalog import PERMISSIONS
from ..permissions import permission_required
from .roles import CODE_USED, DATABASE_CONFLICT, ConfirmForm

INITIAL, SAVE = "initial", "save"
# Mòduls del catàleg, en l'ordre del pla (el prefix del codi del permís).
MODULES = {
    "core": gettext_lazy("00 Base comuna"),
    "members": gettext_lazy("01 Socis i carnet"),
    "treasury": gettext_lazy("04 Tresoreria"),
    "payments": gettext_lazy("05 Pagaments"),
    "licences": gettext_lazy("06 Llicències"),
    "settings": gettext_lazy("Ajustos"),
}
NOT_EDITABLE = gettext_lazy(
    "Aquest canvi no es pot fer: hi ha una cel·la protegida o que no existeix."
)


class MatrixConfirmForm(ConfirmForm):
    reviewed = forms.BooleanField(
        label=gettext_lazy("He revisat el resum i els comptes afectats"),
        error_messages={"required": gettext_lazy("Confirma que has revisat el resum.")},
    )


def _read(data, current, editable):
    """Matriu proposada a partir del formulari. Una cel·la que no hi és es queda com està; una
    que no és editable fa que no es desi res."""
    proposed, bad = dict(current), False
    for name, value in data.items():
        if not name.startswith("c|"):
            continue
        key = tuple(name[2:].split("|", 1))
        if key not in editable:
            bad = True
        elif value:
            proposed[key] = value
        else:
            proposed.pop(key, None)
    return proposed, bad


@never_cache
@permission_required(matrix.EDIT)
@require_http_methods(["GET", "POST"])
def permission_matrix_view(request):
    all_roles = matrix.management_roles()
    editable = {(r.code, p.code) for r in all_roles for p in matrix.editable_permissions()}
    # Filtres (a l'adreça, també en desar): un mòdul i, si cal, un rol. Sense, la matriu sencera
    # no cap a la pantalla d'un mòbil. Les cel·les que no surten no es toquen.
    module = request.GET.get("modul")
    module = module if module in MODULES else next(iter(MODULES))
    role_code = request.GET.get("rol", "")
    role_list = [role for role in all_roles if role_code in ("", role.code)] or all_roles
    perms = [perm for perm in PERMISSIONS if perm.module == module]
    shown = {(r.code, p.code) for r in role_list for p in perms} & editable
    current = matrix.current_cells()
    step = request.POST.get("step") if request.method == "POST" else None
    form = MatrixConfirmForm(request.POST if step == SAVE else None)
    bad = False
    if step == INITIAL:  # només les cel·les que es veuen, les mateixes que s'enviaran en desar
        initial = matrix.initial_cells()
        proposed = {key: scope for key, scope in current.items() if key not in shown}
        proposed.update({key: initial[key] for key in shown if key in initial})
    elif step:
        proposed, bad = _read(request.POST, current, editable)
    else:
        proposed = current
    try:
        base = int(request.POST.get("version", "")) if step else matrix.latest_version()
    except ValueError:
        base = -1
    changes = matrix.diff(current, proposed)
    if step == SAVE:
        problem = None
        if bad:
            problem = [NOT_EDITABLE]
        else:
            try:
                matrix.check(proposed, base_version=base, current=current)
            except ValidationError as exc:
                problem = exc.messages
        if problem:
            form.is_valid()  # també els errors de la nota i la casella, si n'hi ha
            form.add_error(None, problem)
        elif form.is_valid():
            error = confirm_code(request, request.user, AREA_ADMIN, form.cleaned_data["code"])
            if error is not None:
                form.add_error("code" if error == WRONG_CODE else None, error)
            else:
                try:
                    version = matrix.save(
                        proposed,
                        by=request.user,
                        note=form.cleaned_data["note"],
                        base_version=base,
                    )
                except ValidationError as exc:
                    form.add_error(None, [*exc.messages, CODE_USED])
                except OperationalError:
                    form.add_error(None, [DATABASE_CONFLICT, CODE_USED])
                else:
                    messages.success(
                        request,
                        _(
                            "Desada la versió %(number)s de la matriu. S'ha avisat per correu els "
                            "comptes que ho han de saber."
                        )
                        % {"number": version.number},
                    )
                    return redirect(request.get_full_path())
    return render(
        request,
        "core/permission_matrix.html",
        {
            "roles": role_list,
            "rows": _rows(perms, role_list, current, proposed),
            "modules": MODULES.items(),
            "module": module,
            "all_roles": all_roles,
            "role_code": role_code if len(role_list) == 1 else "",
            "changes": [matrix.describe(cell) for cell in changes],
            "affected": [a.login for a in matrix.affected_accounts(changes)] if changes else [],
            "version": base if step else matrix.latest_version(),
            "form": form,
            "step": step,
        },
    )


def _rows(perms, role_list, current, proposed):
    rows = []
    for perm in perms:
        row = {"perm": perm, "cells": []}
        if not perm.protected:
            options = [("", matrix.scope_label(None))] + [
                (scope, matrix.scope_label(scope)) for scope in perm.allowed_scopes
            ]
            for role in role_list:
                key = (role.code, perm.code)
                before, value = current.get(key), proposed.get(key)
                row["cells"].append(
                    {
                        "name": f"c|{role.code}|{perm.code}",
                        "role": role,
                        "value": value or "",
                        "options": options,
                        "before": matrix.scope_label(before) if before != value else "",
                    }
                )
        rows.append(row)
    return rows

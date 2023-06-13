from . import helpers
from django.http import JsonResponse
from Access.paginator_decorators import paginator
from django.contrib.auth.decorators import login_required

@login_required
@paginator
def get_ssh_machines(request):
    try:
        data = request.GET
        search = (data["search"] if data.get("search") else "")
        machine_list = []
        all_machines = []

        for key, value in helpers.ssh_machine_list.items():
            if (key == "hostname" and value == "ip"):
                continue

            if ((search.lower() in key.lower()) or (search.lower() in value.lower())):
                machine_list.append({
                    "name": key,
                    "tagname": key,
                    "ip": value
                })

            all_machines.append({
                "name": key,
                "tagname": key,
                "ip": value
            })

        response = {"machineList": machine_list, "rowList": "machineList"}

        if not machine_list:
            response["machineList"] = all_machines
            response["search_error"] = ("Please try adjusting your search",
                                        "to find what you're looking for.")


        return response
    except Exception:
        return JsonResponse({"error": "Failed to Fetch SSH Machines"}, status=500)

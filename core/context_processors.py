import re

from django.urls import reverse


def get_sbadmin2_sidebar_urls(request):
    user = request.user
    sidebar_urls = [
        {
            "name": "Some basic Dashboard",
            "icon": "fas fa-layer-group",
            "href": reverse("admin:index"),
            "type": "LINK",
        },
        {"type": "BREAK"},
        {"name": "Some Heading", "type": "HEADING"},
    ]

    # TODO: TEMPLATE KEEP ADDING NEW URLS HERE
    # if user.has_perm("main.view_testmodel"):
    #     sidebar_urls.append(
    #         {
    #             "name": "Some category",
    #             "icon": "fas fa-fw fa-route",
    #             "type": "DROP_LINK",
    #             "childs": [
    #                 {"name": "Test Model", "href": reverse("main:test_model_list")},
    #                 # {"name": "Some other url", "href": reverse("testing_list")},
    #             ],
    #         }
    #     )

    return sidebar_urls


def is_mobile(request):
    MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)
    return "HTTP_USER_AGENT" in request.META and MOBILE_AGENT_RE.match(
        request.META["HTTP_USER_AGENT"]
    )


def is_mobile_context(request):
    return {"is_mobile": is_mobile(request)}


def sbadmin2_sidebar_data(request):
    if not (
        request.user
        and request.user.is_authenticated
        and request.user.render_sbadmin2_ui
    ):
        return {}

    sbadmin2_sidebar_urls = get_sbadmin2_sidebar_urls(request)

    current_url = request.path
    active_index = None

    add_url_index = current_url.find("/add")
    edit_url_index = current_url.find("/edit")

    if add_url_index >= 0:
        current_url = f"{current_url[:add_url_index]}/list/"
    elif edit_url_index >= 0:
        current_url = f"{current_url[:edit_url_index]}/list/"

    for i, url in enumerate(sbadmin2_sidebar_urls):
        if url["type"] == "DROP_LINK":
            for child in url["childs"]:
                if child["href"] == current_url:
                    active_index = i
                    break
        elif url["type"] == "LINK":
            pass
    if active_index:
        sbadmin2_sidebar_urls[active_index]["has_child_active"] = True

    return {"sbadmin2_sidebar_urls": sbadmin2_sidebar_urls, "current_url": current_url}

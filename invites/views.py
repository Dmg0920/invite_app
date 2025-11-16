from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuickInviteeForm, SchoolBulkAddForm, SchoolForm
from .models import Invitee, School


@login_required
def home(request: HttpRequest) -> HttpResponse:
    quick_add_form = QuickInviteeForm()
    school_form = SchoolForm()
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "invitees":
            quick_add_form = QuickInviteeForm(request.POST)
            if quick_add_form.is_valid():
                school: School = quick_add_form.cleaned_data["school"]
                status = quick_add_form.cleaned_data["status"]
                names = quick_add_form.cleaned_data["names_text"]
                created_count = 0
                updated_count = 0
                for name in names:
                    invitee, created = Invitee.objects.get_or_create(
                        name=name,
                        school=school,
                        defaults={"status": status},
                    )
                    if created:
                        created_count += 1
                    else:
                        if invitee.status != status:
                            invitee.status = status
                            invitee.save(update_fields=["status"])
                            updated_count += 1
                if created_count or updated_count:
                    messages.success(
                        request,
                        f"已為 {school.name} 新增 {created_count} 位、更新 {updated_count} 位狀態。",
                    )
                else:
                    messages.info(request, "沒有產生變更，可能所有名字都已存在且狀態相同。")
                return redirect("home")
        elif form_type == "school":
            school_form = SchoolForm(request.POST)
            if school_form.is_valid():
                school = school_form.save()
                messages.success(request, f"{school.name} 已加入列表")
                return redirect("home")
        else:
            messages.error(request, "未知的表單提交")

    school_rows = []
    status_definitions = [
        {
            "key": Invitee.Status.PENDING,
            "label": "邀約中",
            "css": "status-pending",
            "color": "#8da9c4",
        },
        {
            "key": Invitee.Status.INVITED,
            "label": "已邀約",
            "css": "status-invited",
            "color": "#f6ad55",
        },
        {
            "key": Invitee.Status.ACCEPTED,
            "label": "會去",
            "css": "status-accepted",
            "color": "#38b2ac",
        },
        {
            "key": Invitee.Status.DECLINED,
            "label": "拒絕",
            "css": "status-declined",
            "color": "#f56565",
        },
    ]
    overall_counts = {item["key"]: 0 for item in status_definitions}

    for school in School.objects.order_by("name"):
        queryset = school.invitees.all()
        counts = {
            Invitee.Status.PENDING: queryset.filter(
                status=Invitee.Status.PENDING
            ).count(),
            Invitee.Status.INVITED: queryset.filter(
                status=Invitee.Status.INVITED
            ).count(),
            Invitee.Status.ACCEPTED: queryset.filter(
                status=Invitee.Status.ACCEPTED
            ).count(),
            Invitee.Status.DECLINED: queryset.filter(
                status=Invitee.Status.DECLINED
            ).count(),
        }
        for key in overall_counts:
            overall_counts[key] += counts[key]
        counts_list = [
            {
                "key": item["key"],
                "label": item["label"],
                "css": item["css"],
                "value": counts[item["key"]],
            }
            for item in status_definitions
        ]
        school_rows.append(
            {
                "slug": school.slug,
                "label": school.name,
                "counts": counts,
                "counts_list": counts_list,
                "total": sum(counts.values()),
            }
        )

    chart_labels = [school["label"] for school in school_rows]
    chart_datasets = []
    for item in status_definitions:
        dataset = {
            "label": item["label"],
            "backgroundColor": item["color"],
            "data": [school["counts"][item["key"]] for school in school_rows],
            "borderRadius": 8,
            "barThickness": 26,
        }
        chart_datasets.append(dataset)

    chart_config = {
        "labels": chart_labels,
        "datasets": chart_datasets,
    }
    overall_chart_config = {
        "labels": [item["label"] for item in status_definitions],
        "datasets": [
            {
                "data": [overall_counts[item["key"]] for item in status_definitions],
                "backgroundColor": [item["color"] for item in status_definitions],
                "borderWidth": 0,
            }
        ],
    }

    status_metrics = [
        {
            "key": item["key"],
            "label": item["label"],
            "count": overall_counts[item["key"]],
            "css": item["css"],
        }
        for item in status_definitions
    ]

    context = {
        "schools": school_rows,
        "status_definitions": status_definitions,
        "overall_counts": overall_counts,
        "status_metrics": status_metrics,
        "chart_config": chart_config,
        "overall_chart_config": overall_chart_config,
        "quick_add_form": quick_add_form,
        "school_form": school_form,
    }
    return render(request, "invites/home.html", context)


@login_required
def school_dashboard(request: HttpRequest, school_slug: str) -> HttpResponse:
    school = get_object_or_404(School, slug=school_slug)

    add_form = SchoolBulkAddForm()
    invitees = Invitee.objects.filter(school=school).order_by("name")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_many":
            add_form = SchoolBulkAddForm(request.POST)
            if add_form.is_valid():
                status = add_form.cleaned_data["status"]
                names = add_form.cleaned_data["names_text"]
                created_count = 0
                updated_count = 0
                for name in names:
                    invitee, created = Invitee.objects.get_or_create(
                        name=name,
                        school=school,
                        defaults={"status": status},
                    )
                    if created:
                        created_count += 1
                    else:
                        if invitee.status != status:
                            invitee.status = status
                            invitee.save(update_fields=["status"])
                            updated_count += 1
                if created_count or updated_count:
                    messages.success(
                        request,
                        f"{school.name} 新增 {created_count} 位、更新 {updated_count} 位狀態。",
                    )
                else:
                    messages.info(request, "沒有產生變更，可能所有名字都已存在且狀態相同。")
                return redirect("school_dashboard", school_slug=school_slug)
        elif action == "bulk_update":
            selected_ids = request.POST.getlist("selected")
            new_status = request.POST.get("bulk_status")
            status_map = dict(Invitee.Status.choices)
            if not selected_ids:
                messages.warning(request, "請先勾選至少一位成員")
                return redirect("school_dashboard", school_slug=school_slug)
            if new_status not in status_map:
                messages.error(request, "請選擇要套用的狀態")
                return redirect("school_dashboard", school_slug=school_slug)
            invitees_to_update = Invitee.objects.filter(
                id__in=selected_ids, school=school
            )
            updated = 0
            for invitee in invitees_to_update:
                if invitee.status != new_status:
                    invitee.status = new_status
                    invitee.save(update_fields=["status"])
                    updated += 1
            if updated:
                messages.success(request, f"已更新 {updated} 位成員狀態")
            else:
                messages.info(request, "沒有偵測到狀態變更")
            return redirect("school_dashboard", school_slug=school_slug)
        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected")
            if not selected_ids:
                messages.warning(request, "請先勾選至少一位成員")
                return redirect("school_dashboard", school_slug=school_slug)
            qs = Invitee.objects.filter(id__in=selected_ids, school=school)
            count = qs.count()
            if count:
                qs.delete()
                messages.success(request, f"已刪除 {count} 位成員")
            else:
                messages.info(request, "沒有符合條件的名單")
            return redirect("school_dashboard", school_slug=school_slug)
        else:
            messages.error(request, "未知的操作")

    context = {
        "school_label": school.name,
        "school_slug": school.slug,
        "invitees": invitees,
        "status_choices": Invitee.Status.choices,
        "add_form": add_form,
    }
    return render(request, "invites/school_detail.html", context)


def signup(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "註冊完成，已自動登入")
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})

import re

from django import forms
from django.utils.text import slugify

from .models import Invitee, School


class MultiNamesMixin:
    placeholder = "以空格或換行分隔，例如：王琮穎 林漢臣 楊淨嵐"

    def clean_names_text(self):
        raw_text = self.cleaned_data.get("names_text", "")
        names = [name.strip() for name in re.split(r"[\s,]+", raw_text) if name.strip()]
        if not names:
            raise forms.ValidationError("請輸入至少一位姓名，可用空格或換行分隔")
        return names


class QuickInviteeForm(MultiNamesMixin, forms.Form):
    school = forms.ModelChoiceField(
        queryset=School.objects.none(),
        label="學校",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status = forms.ChoiceField(
        choices=Invitee.Status.choices,
        label="預設狀態",
        widget=forms.Select(attrs={"class": "form-select"}),
        initial=Invitee.Status.PENDING,
    )
    names_text = forms.CharField(
        label="姓名列表",
        widget=forms.Textarea(
            attrs={
                "placeholder": MultiNamesMixin.placeholder,
                "rows": 3,
                "class": "form-control",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["school"].queryset = School.objects.order_by("name")


class SchoolBulkAddForm(MultiNamesMixin, forms.Form):
    status = forms.ChoiceField(
        choices=Invitee.Status.choices,
        label="預設狀態",
        widget=forms.Select(attrs={"class": "form-select"}),
        initial=Invitee.Status.PENDING,
    )
    names_text = forms.CharField(
        label="姓名列表",
        widget=forms.Textarea(
            attrs={
                "placeholder": MultiNamesMixin.placeholder,
                "rows": 3,
                "class": "form-control",
            }
        ),
    )


class SchoolForm(forms.ModelForm):
    slug = forms.CharField(
        label="網址短碼",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "例：ntpu",
                "class": "form-control",
            }
        ),
        help_text="可留白，系統會依名稱自動建立。",
    )

    class Meta:
        model = School
        fields = ["name", "slug"]
        labels = {"name": "學校名稱"}
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "例：國立台北大學", "class": "form-control"}
            )
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug", "")
        name = self.cleaned_data.get("name", "")
        if not slug:
            slug = slugify(name, allow_unicode=True)
        if not slug:
            raise forms.ValidationError("請輸入或調整網址短碼")
        slug = slug.lower()
        if School.objects.filter(slug=slug).exists():
            raise forms.ValidationError("此短碼已存在，請改用其他代號")
        return slug

from django.db import models


class School(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Invitee(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "邀約中"
        INVITED = "invited", "已邀約"
        DECLINED = "declined", "拒絕"
        ACCEPTED = "accepted", "會去"

    name = models.CharField(max_length=100)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="invitees"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    sheet_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("name", "school")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.school})"

    @property
    def display_status(self):
        if self.status == self.Status.INVITED:
            return "已邀約"
        return self.get_status_display()

    @property
    def status_css(self):
        return {
            self.Status.PENDING: "status-pending",
            self.Status.INVITED: "status-invited",
            self.Status.ACCEPTED: "status-accepted",
            self.Status.DECLINED: "status-declined",
        }.get(self.status, "")

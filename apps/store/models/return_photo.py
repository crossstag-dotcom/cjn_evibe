from django.db import models


class ReturnPhoto(models.Model):

    return_request = models.ForeignKey(
        "ReturnRequest",
        related_name="photos",
        on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to="returns/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"Return Photo {self.id}"
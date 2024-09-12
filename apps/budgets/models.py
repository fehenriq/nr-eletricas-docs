from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    document = models.CharField(max_length=18, blank=True, null=True)

    def __str__(self):
        return self.name


class Budget(models.Model):
    BUDGET_TYPES = [
        ("materials", "With Materials"),
        ("services", "Service Only"),
    ]

    client = models.ForeignKey(Client, related_name="budgets", on_delete=models.CASCADE)
    budget_date = models.DateField()
    validity_days = models.PositiveIntegerField(default=30)
    service_description = models.TextField(blank=True, null=True)
    workforce = models.FloatField()
    total_materials = models.FloatField(blank=True, null=True)
    total_amount = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to="budgets/", blank=True, null=True)

    budget_type = models.CharField(
        max_length=20, choices=BUDGET_TYPES, default="materials"
    )

    def recalculate_totals(self):
        if self.budget_type == "materials":
            self.total_materials = sum(
                material.total_price for material in self.materials.all()
            )
            self.total_amount = self.total_materials + self.workforce
        elif self.budget_type == "services":
            self.total_amount = (
                sum(service.price or 0 for service in self.services.all())
                + self.workforce
            )
        self.save()

    def __str__(self):
        return f"Budget {self.id} for {self.client.name} - {self.budget_date}"


class Material(models.Model):
    budget = models.ForeignKey(
        Budget, related_name="materials", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.FloatField()
    total_price = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.total_price}"


class Service(models.Model):
    budget = models.ForeignKey(
        Budget, related_name="services", on_delete=models.CASCADE
    )
    description = models.CharField(max_length=255)
    price = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.description} - {self.price if self.price else 'N/A'}"

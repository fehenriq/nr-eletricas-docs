from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    document = models.CharField(max_length=18, blank=True, null=True)

    def __str__(self):
        return self.name


class Budget(models.Model):
    client = models.ForeignKey(Client, related_name="budgets", on_delete=models.CASCADE)
    budget_date = models.DateField()
    validity_days = models.PositiveIntegerField(default=30)
    service_description = models.TextField(blank=True, null=True)
    workforce = models.FloatField()
    total_items = models.FloatField(blank=True, null=True)
    total_amount = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to="budgets/", blank=True, null=True)

    def recalculate_totals(self):
        self.total_items = sum(
            item.total_price for item in self.items.all()
        )
        self.total_amount = self.total_items + self.workforce
        self.save()

    def __str__(self):
        return f"Budget {self.id} for {self.client.name} - {self.budget_date}"


class BudgetItem(models.Model):
    budget = models.ForeignKey(
        Budget, related_name="items", on_delete=models.CASCADE
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

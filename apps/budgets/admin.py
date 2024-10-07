from datetime import datetime

from django.contrib import admin
from django.http import HttpResponse

from .models import Budget, BudgetItem, Client
from .pdf import generate_pdf


class MaterialInline(admin.TabularInline):
    model = BudgetItem
    extra = 1
    readonly_fields = ["total_price"]
    fields = ["description", "quantity", "unit_price", "total_price"]


class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "address")
    search_fields = ("name", "document", "address")


def generate_txt(budget):
    lines = []

    for item in budget.items.all():
        lines.append(f"{item.description}")

    total = budget.total_amount
    lines.append(f"\nCliente: {budget.client.document}")
    lines.append(f"\nTotal: {total}")

    return "\n".join(lines)


class BudgetAdmin(admin.ModelAdmin):
    list_display = ("client", "budget_date", "total_amount")
    inlines = [MaterialInline]
    search_fields = ("client__name", "service_description")
    readonly_fields = ["total_items", "total_amount"]
    actions = ["generate_pdf_action", "generate_txt_action"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_totals()

    @admin.action(description="Generate PDF for selected budgets")
    def generate_pdf_action(self, request, queryset):
        for budget in queryset:
            generate_pdf(budget)
        self.message_user(
            request, "PDFs generated successfully for the selected budgets."
        )

    @admin.action(description="Generate TXT for selected budgets")
    def generate_txt_action(self, request, queryset):
        for budget in queryset:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_name = budget.client.name.replace(" ", "_")
            filename = f"ORCAMENTO_{budget.id}_{client_name}_{timestamp}.txt"

            txt_content = generate_txt(budget)

            response = HttpResponse(txt_content, content_type="text/plain")
            response["Content-Disposition"] = f"attachment; filename={filename}"

            return response

        self.message_user(
            request, "TXTs generated successfully for the selected budgets."
        )


admin.site.register(Client, ClientAdmin)
admin.site.register(Budget, BudgetAdmin)

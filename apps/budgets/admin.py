from django.contrib import admin

from .models import Budget, Client, BudgetItem
from .pdf import generate_pdf


class MaterialInline(admin.TabularInline):
    model = BudgetItem
    extra = 1
    readonly_fields = ["total_price"]
    fields = ["description", "quantity", "unit_price", "total_price"]


class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "address")
    search_fields = ("name", "document", "address")


class BudgetAdmin(admin.ModelAdmin):
    list_display = ("client", "budget_date", "total_amount")
    inlines = [MaterialInline]
    search_fields = ("client__name", "service_description")
    readonly_fields = ["total_items", "total_amount"]
    actions = ["generate_pdf_action"]

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


admin.site.register(Client, ClientAdmin)
admin.site.register(Budget, BudgetAdmin)

from datetime import datetime
from io import BytesIO

from django.contrib import admin
from django.core.files.base import ContentFile
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import Budget, Client, Material, Service


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1
    readonly_fields = ["total_price"]
    fields = ["description", "quantity", "unit_price", "total_price"]


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    fields = ["description", "price"]


class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "address")
    search_fields = ("name", "document", "address")


class BudgetAdmin(admin.ModelAdmin):
    list_display = ("client", "budget_date", "total_amount")
    inlines = [MaterialInline, ServiceInline]
    search_fields = ("client__name", "service_description")
    readonly_fields = ["total_materials", "total_amount"]
    actions = ["generate_pdf_action"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalculate_totals()

    @admin.action(description="Generate PDF for selected budgets")
    def generate_pdf_action(self, request, queryset):
        for budget in queryset:
            self.generate_pdf(budget)
        self.message_user(
            request, "PDFs generated successfully for the selected budgets."
        )

    def generate_pdf(self, budget):
        template = get_template("budgets/budget_pdf.html")
        html = template.render({"budget": budget})

        result = BytesIO()
        pdf = pisa.CreatePDF(BytesIO(html.encode("utf-8")), dest=result)

        if not pdf.err:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_name = budget.client.name.replace(" ", "_")
            budget.pdf_file.save(
                f"ORCAMENTO_{budget.id}_{client_name}_{timestamp}.pdf",
                ContentFile(result.getvalue()),
            )
            result.close()


admin.site.register(Client, ClientAdmin)
admin.site.register(Budget, BudgetAdmin)

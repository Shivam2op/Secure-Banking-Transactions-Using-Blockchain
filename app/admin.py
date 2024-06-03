from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from app.models import *
from app.forms.AdminForms import MyUserCreateForm, MyUserChangeForm


@admin.register(MyUser)
class MyUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreateForm
    change_form_template = 'admin/auth/user/change_form.html'
    change_list_template = 'admin/auth/user/change_list.html'
    ordering = ('-pk',)

    fieldsets = UserAdmin.fieldsets + (
        ('User Type', {'fields': ('user_type',)}),
        ('Assigned To', {'fields': ('assigned_to',)}),
    )


admin.site.register(Address)
admin.site.register(PII)
admin.site.register(Account)
admin.site.register(Card)
admin.site.register(Transaction)
admin.site.register(UserRequest)
admin.site.register(KnownAccount)
admin.site.register(PublicKey)
admin.site.register(MerchantPaymentAccount)

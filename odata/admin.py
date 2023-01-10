from bson import ObjectId
from django import forms
from django.contrib import admin
from django.contrib.admin import helpers, widgets
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group, User

from import_export.admin import ImportExportModelAdmin

from odata.models import *
from odata.exportimport.productresources import ProductResources

import logging

log = logging.getLogger(__name__)
# convert the errors to text
from django.utils.encoding import force_text

admin.site.disable_action('delete_selected')


# Register your models here.

class ProductModelForm(forms.ModelForm):
    categories = Categories.objects.all()
    categories_choice = [('', '-----')]
    if categories:
        categories_choice = [(None, '-----')] + [(x._id, x.category_name) for x in categories]
    category = forms.ChoiceField(choices=categories_choice)

    class Meta:
        model = Product
        fields = '__all__'

    def is_valid(self):
        log.info(force_text(self.errors))
        return super(ProductModelForm, self).is_valid()
    # def clean(self):
    #     # Validation goes here :)
    #     raise forms.ValidationError("TEST EXCEPTION!")


class ProductImageForm(forms.ModelForm):
    products = Product.objects.all()
    products_choice = [('', '-----')]
    if products:
        products_choice += [(x._id, x.product_name) for x in products]
    _id = forms.CharField(max_length=2048)

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        # add a default rating if one hasn't been passed in
        # initial['product'] = str(initial.get('product', 0))
        if kwargs.get('instance'):
            initial['_id'] = str(str(kwargs.get('instance')._id))
            kwargs['initial'] = initial
        super(ProductImageForm, self).__init__(
            *args, **kwargs
        )

    class Meta:
        model = ProductImage
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        # cleaned_data["_id"] = ObjectId(cleaned_data["_id"])
        # if cleaned_data.get('product'):
        #     product = Product.objects.get(pk=ObjectId(cleaned_data['product']))
        #     cleaned_data['product'] = product

        return cleaned_data


from django.forms.models import BaseInlineFormSet


class CompositionElementFormSet(BaseInlineFormSet):
    '''
    Validate formset data here
    '''

    def clean(self):
        super(CompositionElementFormSet, self).clean()

        percent = 0
        for form in self.forms:
            if form._errors not in list(form.fields.keys()):
                form._errors = {}
            if not hasattr(form, 'cleaned_data'):
                continue


class ProductModelInline(admin.StackedInline):
    model = ProductImage
    formset = CompositionElementFormSet
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        # ex. the name of column is "image"
        if obj.image:
            return mark_safe('<img src="{0}" width="150" height="150" style="object-fit:contain" />'.format(obj.image))
        else:
            return '(No image)'

    image_preview.short_description = 'Preview'


class ProductSizeForm(forms.ModelForm):
    products = Product.objects.all()
    product_variant = ProductVariant.objects.all()
    products_choice = [('', '-----')]
    products_size = [('', '-----')]
    if products:
        products_name = [(None, '-----')] + [(x._id, x.product_name) for x in products]
        size = forms.ChoiceField(choices=products_name)
        color = forms.ChoiceField(choices=products_name)


class ProductVariantInline(admin.StackedInline):
    form = ProductSizeForm
    model = ProductVariant
    formset = CompositionElementFormSet


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    icon_name = 'store'
    resource_class = ProductResources
    inlines = [ProductModelInline, ProductVariantInline]
    list_display = ('product_name', 'quantity', 'price', 'msrp', 'image_tag', 'created_at', 'updated_at')
    form = ProductModelForm
    list_per_page = 15
    actions = ['make_deleted']

    def make_deleted(modeladmin, request, queryset):
        obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
        for i in obj_ids:
            query = Product.objects.get(pk=i)
            pro_img = ProductImage.objects.filter(product=query).delete()
            query.delete()

    make_deleted.short_description = 'Delete selected product'

    class Media:
        js = ('js/tinmc.js',)

    def image_tag(self, obj):
        image_str = ''
        if obj.picture:
            image_str = '<img src="{0}" style="width: 45px; height:45px;" />'.format(obj.picture)
        product_images = ProductImage.objects.filter(product=obj)
        if product_images:
            for pro_img in product_images:
                if pro_img.image:
                    try:
                        image_str += ' <img src="{0}" style="width: 45px; height:45px;" />'.format(pro_img.image)
                    except:
                        pass
        return format_html(image_str)

    def save_formset(self, request, form, formset, change):
        for inline_form in formset.forms:
            if inline_form.has_changed():
                inline_form.instance.user = request.user
        super().save_formset(request, form, formset, change)

    def save_model(self, request, obj, form, change):
        super(ProductAdmin, self).save_model(request, obj, form, change)


class CategoryForm(forms.ModelForm):
    categories = Categories.objects.all()
    categories_choice = [('', '-----')]
    if categories:
        categories_choice = [(None, '-----')] + [(x._id, x.category_name) for x in categories]
    parent = forms.ChoiceField(choices=categories_choice, required=False)

    class Meta:
        model = Categories
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data.get('parent'):
            product = Categories.objects.get(pk=ObjectId(cleaned_data['parent']))
            cleaned_data['parent'] = product
        else:
            cleaned_data['parent'] = None

        return cleaned_data


@admin.register(Categories)
class CategoryAdmin(admin.ModelAdmin):
    icon_name = 'device_hub'
    search_fields = ('category_name',)
    list_per_page = 15
    form = CategoryForm
    list_display = ('category_name', 'parent', 'category_name_de')
    actions = ['make_deleted']

    def get_object(self, request, object_id, from_field=None):
        """
        Return an instance matching the field and value provided, the primary
        key is used if no field is provided. Return ``None`` if no match is
        found or the object_id fails validation.
        """

        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)
        try:
            object_id = field.to_python(object_id)
            return queryset.get(**{field.name: ObjectId(object_id)})
        except (model.DoesNotExist, ValueError):
            return None

    def make_deleted(modeladmin, request, queryset):
        obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
        for i in obj_ids:
            query = Categories.objects.get(pk=i)
            query.delete()

    make_deleted.short_description = 'Delete selected category'

    def get_form(self, request, obj=None, **kwargs):
        form = super(CategoryAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].widget.can_add_related = False
        return form


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    icon_name = 'person'
    exclude = ('user',)
    list_per_page = 15
    actions = ['make_deleted']

    def save_model(self, request, obj, form, change):
        import random, string
        x = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user = User.objects.create(username=x)
        obj.user = user
        super().save_model(request, obj, form, change)

    def make_deleted(modeladmin, request, queryset):
        obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
        for i in obj_ids:
            query = Customer.objects.get(pk=i)
            query.delete()

    make_deleted.short_description = 'Delete selected customer'


# @admin.register(ProductVariant)
# class ProductVariantAdmin(admin.ModelAdmin):
#     icon_name = 'child_friendly'
#     list_per_page = 15
#     search_fields = ('parent_product__product_name',)
#     form = ProductVariantForm
#     actions = ['make_deleted']
#
#     def make_deleted(modeladmin, request, queryset):
#         obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
#         for i in obj_ids:
#             query = ProductVariant.objects.get(pk=i)
#             query.delete()
#
#     make_deleted.short_description = 'Delete selected product variant'


@admin.register(NewsletterSubscription)
class NewsletterAdmin(admin.ModelAdmin):
    icon_name = 'picture_in_picture'
    list_per_page = 15

    actions = ['make_deleted']

    def make_deleted(modeladmin, request, queryset):
        obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
        for i in obj_ids:
            query = NewsletterSubscription.objects.get(pk=i)
            query.delete()

    make_deleted.short_description = 'Delete selected NewsLetter'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    icon_name = 'payment'
    actions = ['make_deleted']

    def make_deleted(modeladmin, request, queryset):
        obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
        for i in obj_ids:
            query = Payment.objects.get(pk=i)
            query.delete()

    make_deleted.short_description = 'Delete selected payment'


@admin.register(UserForgotPassword)
class UserForgotPasswordAdmin(admin.ModelAdmin):
    icon_name = 'password'
# UnRegister your model.
# admin.site.unregister(User)
# admin.site.unregister(Group)

# @admin.register(ProductImage)
# class ProductImageAdmin(admin.ModelAdmin):
#     icon_name = 'child_friendly'
#     list_per_page = 15
#     search_fields = ('product__product_name',)
#     list_display = ("product", "image_tag")
#     form = ProductImageForm
#     actions = ['make_deleted']

#     def image_tag(self,obj):
#         image_str = ''
#         if obj.image:
#             image_str = '<img src="{0}" style="width: 45px; height:45px;" />'.format(obj.image)

#         return format_html(image_str)
#     def make_deleted(modeladmin, request, queryset):
#         obj_ids = [ObjectId(i) for i in request.POST.getlist('_selected_action')]
#         for i in obj_ids:
#             query = ProductImage.objects.get(pk=i)
#             query.delete()

#     make_deleted.short_description ='Delete selected product variant'

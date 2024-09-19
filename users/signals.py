from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group

User = get_user_model()

@receiver(post_save, sender=User)
def assign_permissions(sender, instance, created, **kwargs):
    if created:
        # Define permissions for each role
        permissions_map = {
            'buyer': [
                'can_view_property', 'can_view_purchase_history',
                'can_communicate_with_seller', 'assign_a_lawyer',
                'upload_payment_document', 'view_transaction'
            ],
            'seller': [
                'can_confirm_land_information',
                'can_communicate_with_buyer',
                'assign_a_lawyer', 'upload_payment_document',
                'view_transaction'
            ],
            'lawyer': [
                'draft_a_contract', 'view_transaction',
                'can_communicate_with_seller_and_lawyer'
            ],
            'admin': ['add_user', 'change_user', 'delete_user', 'view_user']
        }

        role = instance.role
        if role in permissions_map:
            permissions = permissions_map[role]
            for perm in permissions:
                try:
                    permission = Permission.objects.get(codename=perm)
                    instance.user_permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"Permission '{perm}' does not exist.")

            # Group creation and assignment
            group_name = f"{role}s"  # e.g., "buyers", "sellers", "lawyers"
            group, created = Group.objects.get_or_create(name=group_name)
            instance.groups.add(group)




















# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth.models import Permission, Group
# from .models import CustomUser

# @receiver(post_save, sender=CustomUser)
# def assign_permissions(sender, instance, created, **kwargs):
#     # if created or instance.role_changed():
#     #     instance.user_permissions.clear()
#     #     instance.groups.clear()
        
#         """Define permissions for each role"""
#         permissions_map = {
#             'buyer': [
#                 'can_view_property', 'can_view_purchase_history', 
#                 'can_communicate_with_seller', 'assign_a_lawyer', 
#                 'upload_payment_document', 'view_transaction'
#             ],
#             'seller': [
#                 'can_confirm_land_information',  
#                 'can_communicate_with_buyer', 
#                 'assign_a_lawyer', 'upload_payment_document', 
#                 'view_transaction'
#             ],
#             'lawyer': [
#                 'draft_a_contract', 'view_transaction', 
#                 'can_communicate_with_seller_and_lawyer'
#             ]
#         }

        
#         role = instance.role
#         if role in permissions_map:
#             permissions = permissions_map[role]
#             for perm in permissions:
#                 try:
#                     permission = Permission.objects.get(codename=perm)
#                     instance.user_permissions.add(permission)
#                 except Permission.DoesNotExist:
#                     print(f"Permission '{perm}' does not exist.")

#             """group creation and assignment"""
#             group_name = f"{role}s"  
#             group, created = Group.objects.get_or_create(name=group_name)
#             instance.groups.add(group)

#         instance.save()





# # signals.py

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Permission

# User = get_user_model()

# @receiver(post_save, sender=User)
# def assign_permissions(sender, instance, created, **kwargs):
#     if created:
#         role_permissions = {
#             'admin': ['add_user', 'change_user', 'delete_user', 'view_user'],
#             'lawyer': ['view_user'],
#             'buyer': ['view_user'],
#             'seller': ['view_user'],
#         }

#         if instance.role in role_permissions:
#             for perm in role_permissions[instance.role]:
#                 try:
#                     permission = Permission.objects.get(codename=perm)
#                     instance.user_permissions.add(permission)
#                 except Permission.DoesNotExist:
#                     print(f"Permission {perm} does not exist")

#         instance.save(update_fields=['user_permissions'])




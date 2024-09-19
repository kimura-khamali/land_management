# users/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedAndHasPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('your_permission_name')

class HasLawyerPermissions(BasePermission):
    """
    Custom permission for lawyers.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        lawyer_permissions = [
            'draft_a_contract',
            'view_transaction',
            'can_communicate_with_clients'
        ]
        return any(request.user.has_perm(perm) for perm in lawyer_permissions)

class HasBuyerPermissions(BasePermission):
    """
    Custom permission for buyers.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        buyer_permissions = [
            'can_view_property',
            'can_view_purchase_history',
            'can_communicate_with_seller',
            'assign_a_lawyer',
            'upload_payment_document',
            'view_transaction',
        ]
        return any(request.user.has_perm(perm) for perm in buyer_permissions)

class HasSellerPermissions(BasePermission):
    """
    Custom permission for sellers.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        seller_permissions = [
            'can_view_offers',
            'can_communicate_with_buyer',
            'assign_a_lawyer',
            'upload_payment_document',
            'view_transaction',
        ]
        return any(request.user.has_perm(perm) for perm in seller_permissions)


















# from rest_framework.permissions import BasePermission, SAFE_METHODS

# class IsAuthenticatedAndHasPermission(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.has_perm('your_permission_name')

# class HasLawyerPermissions(BasePermission):
#     """
#     Custom permission for lawyers.
#     """
#     def has_permission(self, request, view):
#         if request.method in SAFE_METHODS:
#             return True
        
#         lawyer_permissions = [
#             'draft_a_contract',
#             'view_transaction',
#             'can_communicate_with_clients'
#         ]
#         return any(request.user.has_perm(perm) for perm in lawyer_permissions)

# class HasBuyerPermissions(BasePermission):
#     """
#     Custom permission for buyers.
#     """
#     def has_permission(self, request, view):
#         if request.method in SAFE_METHODS:
#             return True
        
#         buyer_permissions = [
#             'can_view_property',
#             'can_view_purchase_history',
#             'can_communicate_with_seller',
#             'assign_a_lawyer',
#             'upload_payment_document',
#             'view_transaction',
#         ]
#         return any(request.user.has_perm(perm) for perm in buyer_permissions)

# class HasSellerPermissions(BasePermission):
#     """
#     Custom permission for sellers.
#     """
#     def has_permission(self, request, view):
#         if request.method in SAFE_METHODS:
#             return True
        
#         seller_permissions = [
            
#             'can_view_offers',
#             'can_communicate_with_buyer',
#             'assign_a_lawyer',
#             'upload_payment_document',
#             'view_transaction',
#         ]
#         return any(request.user.has_perm(perm) for perm in seller_permissions)





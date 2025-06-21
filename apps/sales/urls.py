from django.urls import path
from .views import UploadItems, SearchItems, RaiseNeed, ModifyItems, DeleteItems, CheckNeed, GetNeed, ModifyNeed, DeleteNeed, UploadClassSchedule, UploadClassScheduleDict, CheckClassSchedule, RecommendLocation, UpdatePurchase, LoadPurchase, ConfirmPurchase

urlpatterns = [
    path('upload-items', UploadItems.as_view(), name='upload-items'),
    path('search-items', SearchItems.as_view(), name='search-items'),
    path("modify-items", ModifyItems.as_view(), name="modify-items"),
    path("delete-items", DeleteItems.as_view(), name="delete-items"),
    path("upload-courses", UploadClassSchedule.as_view(), name="upload_class_schedule"),
    path("upload-courses-dict", UploadClassScheduleDict.as_view(), name="upload_class_schedule_dict"),
    path("courses", CheckClassSchedule.as_view(), name="check_class_schedule"),
    path('raise-need', RaiseNeed.as_view(), name='raise-need'),
    path("modify-need", ModifyNeed.as_view(), name="modify-need"),
    path("user-needs", CheckNeed.as_view(), name="user-needs"),
    path("get-need", GetNeed.as_view(), name="get-need"),
    path("delete-need", DeleteNeed.as_view(), name="delete-need"),
    path("recommend-location", RecommendLocation.as_view(), name="recommend_location"),
    path("update-purchase", UpdatePurchase.as_view(), name="update-purchase"),
    path("load-purchase", LoadPurchase.as_view(), name="load-purchase"),
    path("confirm-purchase", ConfirmPurchase.as_view(), name="confirm-purchase"),
]
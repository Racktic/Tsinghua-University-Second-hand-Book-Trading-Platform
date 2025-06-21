from rest_framework.views import APIView
from .serializers import UploadItemsSerializer, SearchItemsSerializer, ModifyItemsSerializer, DeleteItemsSerializer, RaiseNeedSerializer, UploadClassScheduleSerializer, UploadClassScheduleDictSerializer, CheckClassScheduleSerializer
from .serializers import UploadItemsSerializer, SearchItemsSerializer, ModifyItemsSerializer, DeleteItemsSerializer, RaiseNeedSerializer, CheckNeedSerializer, ModifyNeedSerializer, GetNeedSerializer, DeleteNeedSerializer, RecommendLocationSerializer
from rest_framework.response import Response
from .serializers import UpdatePurchaseSerializer, LoadPurchaseSerializer, ConfirmPurchaseSerializer
from apps.chat.views import send_notification_when_need_match
from rest_framework import status
from apps.accounts.models import User
from apps.sales.models import Item, Need, Purchase
from django.conf import settings
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from .config import day2num, section2num, nearby_time, num2day, num2section
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Case, When, Value, IntegerField

class CustomPagination(PageNumberPagination):
    page_size = 12  # Default page size
    page_size_query_param = 'page_size'  # Allow client to set page size
    max_page_size = 100  # Maximum page size


class UploadItems(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UploadItemsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # if valid, create the item
            item = serializer.save()
            # After saving an item, check if it fulfills any needs
            # TODO 1: Add logic to check if the item fulfills any needs
            # 查找匹配的需求并发送通知
            self.check_item_need_relation(item)
            return Response({"message": "Item uploaded successfully"},
                            status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def check_item_need_relation(self, item):
        """检查是否有匹配的需求，并向需求发起者发送系统消息"""
        # 使用NeedManager的find_matching_needs方法
        matching_needs = Need.objects.find_matching_needs(item)
        for need in matching_needs:
            send_notification_when_need_match(item, need)
        
class SearchItems(APIView):   
    def __init__(self):
        self.vectorizer = TfidfVectorizer()

    def calculate_similarity(self, item_feature: dict, user_need: dict):
        item_texts = []
        user_texts = []

        for key in item_feature.keys():
            if item_feature[key] is not None:
                item_texts.append(str(item_feature[key]))
        for key in user_need.keys():
            if user_need[key] is not None:
                user_texts.append(str(user_need[key]))

        item_text = " ".join(item_texts)
        user_text = " ".join(user_texts)

        tfidf_matrix = self.vectorizer.fit_transform([item_text, user_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity


    def get(self, request, *args, **kwargs):
        serializer = SearchItemsSerializer(data=request.query_params, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content_type = serializer.validated_data.get('content_type')
        search_keyword = serializer.validated_data.get('search_keyword')
        search_all = serializer.validated_data.get('search_all')
        # 默认只筛选未售出的物品
        sold_filter = {'sold': False}
        if content_type == 'id':
            # If content_type is 'id', search by id
            item_id = int(search_keyword)
            items = Item._default_manager.filter(id=item_id)
            if not items:
                return Response({"message": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        elif content_type == 'user_items':
            # If content_type is 'user_items', return items of the current user
            email = search_keyword
            user = User.objects.filter(email=email).first()
            items = Item._default_manager.filter(user=user,**sold_filter)
        elif search_all:
            # If search_all is True, return all items
            user = serializer.validated_data.get('user')
            if user:
                # Exclude items published by the user themselves
                items = Item.objects.filter(sold=False).exclude(user=user)
                recommended_items = []
                # extract 'title' and 'meta_info' from items
                items_feature = []
                for item in items:
                    title = item.title
                    if item.meta_info:
                        author = item.meta_info.get('author', None)
                        course = item.meta_info.get('course', None)
                        teacher = item.meta_info.get('teacher', None)
                        description = item.meta_info.get('description', None)
                    else:
                        author = None
                        course = None
                        teacher = None
                        description = None
                    items_feature.append({
                        'title': title,
                        'author': author,
                        'course': course,
                        'teacher': teacher,
                        'description': description
                    })
                # recommend given the user's class schedule
                if user.class_schedule:
                    class_schedule = user.class_schedule
                    # consider the course and teacher
                    courses = [class_['course'] for class_ in class_schedule]  
                    teachers = [class_['teacher'] for class_ in class_schedule]
                    for item in items_feature:
                        if item['course'] in courses or item['teacher'] in teachers or item['author'] in teachers:
                            recommended_items.append(item)
                # recommend given the user's needs
                user_needs = Need.objects.filter(user=user)
                if user_needs:
                    user_needs_feature = []
                    for need in user_needs:
                        title = need.title
                        if need.meta_info:
                            author = need.meta_info.get('author', None)
                            course = need.meta_info.get('course', None)
                            teacher = need.meta_info.get('teacher', None)
                            description = need.meta_info.get('description', None)
                        else:
                            author = None
                            course = None
                            teacher = None
                            description = None
                        user_needs_feature.append({
                            'title': title,
                            'author': author,
                            'course': course,
                            'teacher': teacher,
                            'description': description
                        })
                    # recommend function
                    for item in items_feature:
                        for user_need in user_needs_feature:
                            similarity = self.calculate_similarity(item, user_need)
                            if 'similarity' in item:
                                item['similarity'] += similarity
                            else:
                                item['similarity'] = similarity
                    # Sort items by similarity
                    sorted_items_feature = sorted(items_feature, key=lambda x: x['similarity'], reverse=True)
                    # remove key 'similarity' from the items
                    for item in sorted_items_feature:
                        item.pop('similarity', None)
                    recommended_items += sorted_items_feature
                    # remove duplicates
                    recommended_items = list({(item['title'], item['author'], item['course'], item['teacher'], item['description']): item for item in recommended_items}.values())
                    # Convert to Item objects
                    items = [Item.objects.filter(title=item['title']).first() for item in recommended_items]
                    ordered_ids = [item.id for item in items]
                    # need to be the format as queryset and need to maintain the order
                    # eg. change format: [<Item: 数字逻辑与数字集成电路>, <Item: 线性代数入门>] -> <QuerySet [<Item: 数字逻辑与数字集成电路>, <Item: 线性代数入门>]>
                    items = Item.objects.filter(id__in=ordered_ids).annotate(
                        custom_order=Case(
                            *[When(id=ordered_id, then=Value(index)) for index, ordered_id in enumerate(ordered_ids)],
                            output_field=IntegerField()
                        )
                    ).order_by('custom_order')
                else:
                    if recommended_items:
                        # have class schedule but no needs
                        # Convert to Item objects
                        items = [Item.objects.filter(title=item['title']).first() for item in recommended_items]
                        # need to be the format as queryset and need to maintain the order
                        ordered_ids = [item.id for item in items]
                        items = Item.objects.filter(id__in=ordered_ids).annotate(
                            custom_order=Case(
                                *[When(id=ordered_id, then=Value(index)) for index, ordered_id in enumerate(ordered_ids)],
                                output_field=IntegerField()
                            )
                        ).order_by('custom_order')                        
                    else:
                        # have no class schedule and no needs, so return random items
                        items = Item.objects.filter(sold=False).exclude(user=user).order_by('?')
            else:
                # 如果没有登录用户，返回所有商品
                items = Item.objects.filter(sold=False)
            
        else:
            user = serializer.validated_data.get('user')
            if user:
                # Exclude items published by the user themselves
                items = Item.objects.filter(
                    content_type=content_type,
                    search_keyword=search_keyword,
                    sold=False
                ).exclude(user=user)
            else:
                items = Item.objects.filter(
                    content_type=content_type,
                    search_keyword=search_keyword,
                    **sold_filter
                )
        # 加入分页器之后的返回逻辑，不要改
        # 先将 QuerySet 转换为字典 QuerySet, 方便后续使用 .values() 生成 list
        items = list(items.values())
        # 引入自定义分页器
        paginator = CustomPagination()
        paginated_items = paginator.paginate_queryset(items, request)
        data = []
        for item in paginated_items:
            picture_url = None
            if item.get('picture'):
                picture_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{item['picture']}")
                picture_url = picture_url.replace("http://", "https://")
            data.append({
                'title': item['title'],
                'picture': picture_url,
                'username': item['username'],
                'price_lower_bound': item['price_lower_bound'],
                'price_upper_bound': item['price_upper_bound'],
                'meta_info': item['meta_info'],
                'id': item['id'],
            })
            
        # 返回包含分页元数据的响应（count, next, previous, results）
        return paginator.get_paginated_response(data)

class ModifyItems(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ModifyItemsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            item_id = serializer.validated_data.get('id')
            item = Item.objects.filter(id=item_id).first()
            if not item:
                return Response({"message": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
            # 检查物品是否已售出
            if item.sold:
                return Response({"message": "Cannot modify a sold item"}, status=status.HTTP_400_BAD_REQUEST)
            # Update the item with the new data with serializer's update method
            item = serializer.update(item, serializer.validated_data)
            # After modifying an item, check if it fulfills any needs
            self.check_item_need_relation(item)
            return Response({"message": "Item modified successfully",}, 
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def check_item_need_relation(self, item):
        """检查是否有匹配的需求，并向需求发起者发送系统消息"""
        # 使用NeedManager的find_matching_needs方法
        matching_needs = Need.objects.find_matching_needs(item)
        for need in matching_needs:
            send_notification_when_need_match(item, need)

class DeleteItems(APIView):
    def post(self, request, *args, **kwargs):
        serializer = DeleteItemsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            item = serializer.validated_data.get('item')
            item.delete()
            return Response({"message": "Item deleted successfully"}, 
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

class RaiseNeed(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RaiseNeedSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            need = serializer.save()
            # 查找匹配的商品并发送通知
            self.check_item_need_relation(need)
            return Response({"message": "Need raised successfully"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def check_item_need_relation(self, need):
        """检查是否有匹配的商品，并向商品发布者发送系统消息"""
        # 使用ItemManager的find_matching_items方法
        matching_items = Item.objects.find_matching_items(need)
        for item in matching_items:
            send_notification_when_need_match(item, need)
    
class CheckNeed(APIView):
    def get(self, request, *args, **kwargs):
        serializer = CheckNeedSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            needs = Need.objects.filter(user=user)
            needs = list(needs.values())
            data = []
            for need in needs:
                data.append({
                    'title': need['title'],
                    'username': need['username'],
                    'price_lower_bound': need['price_lower_bound'],
                    'price_upper_bound': need['price_upper_bound'],
                    'meta_info': need['meta_info'],
                    'id': need['id'],
                })
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ModifyNeed(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ModifyNeedSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            need_id = serializer.validated_data.get('id')
            need = Need.objects.filter(id=need_id).first()
            if not need:
                return Response({"message": "Need not found"}, status=status.HTTP_404_NOT_FOUND)
            # Check if the need belongs to the user
            user = serializer.validated_data.get('user')
            if need.user != user:
                return Response({"message": "You do not have permission to modify this need"}, 
                                status=status.HTTP_403_FORBIDDEN)
            # Update the need with the new data with serializer's update method
            need = serializer.update(need, serializer.validated_data)
            # After modifying a need, check if it fulfills any items
            self.check_item_need_relation(need)
            return Response({"message": "Need modified successfully",}, 
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def check_item_need_relation(self, need):
        """检查是否有匹配的商品，并向商品发布者发送系统消息"""
        # 使用ItemManager的find_matching_items方法
        matching_items = Item.objects.find_matching_items(need)
        for item in matching_items:
            send_notification_when_need_match(item, need)

class GetNeed(APIView):
    def get(self, request, *args, **kwargs):
        serializer = GetNeedSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            need_id = serializer.validated_data['id']  # 从 validated_data 获取 id
            try:
                need = Need.objects.get(id=need_id)
            except Need.DoesNotExist:
                return Response({"message": "Need not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # 返回需要的信息
            data = {
                'title': need.title,
                'username': need.username,
                'price_lower_bound': need.price_lower_bound,
                'price_upper_bound': need.price_upper_bound,
                'meta_info': need.meta_info,
                'id': need.id,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
class DeleteNeed(APIView):
    def post(self, request, *args, **kwargs):
        serializer = DeleteNeedSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            need = serializer.validated_data.get('need')
            need.delete()
            return Response({"message": "Need deleted successfully"}, 
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UploadClassSchedule(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UploadClassScheduleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                class_schedule = serializer.save()
                return Response({"message": "Class schedule uploaded successfully"}, 
                            status=status.HTTP_201_CREATED)
            except:
                return Response({"message": "Class schedule extraction failed"}, 
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({"message": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        class_schedule = user.class_schedule
        return Response(class_schedule, status=status.HTTP_200_OK)

class UploadClassScheduleDict(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UploadClassScheduleDictSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            courses = serializer.validated_data.get('courses')
            if not isinstance(courses, list):
                return Response({"message": "Courses must be a list."}, status=status.HTTP_400_BAD_REQUEST)
            # 定义必须存在的键集合
            required_keys = {"course", "teacher", "location", "day", "section"}
            for idx, course in enumerate(courses):
                if not isinstance(course, dict):
                    return Response({"message": f"Each course element must be a dict, error at index {idx}."},
                                    status=status.HTTP_400_BAD_REQUEST)
                missing = required_keys - set(course.keys())
                if missing:
                    return Response({"message": f"Missing keys in course at index {idx}: {', '.join(missing)}."},
                                    status=status.HTTP_400_BAD_REQUEST)
            
            # 格式检查通过，保存到用户的 class_schedule 字段
            serializer.save()
            return Response({"message": "Class schedule uploaded successfully"}, 
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
class CheckClassSchedule(APIView):
    def get(self, request, *args, **kwargs):
        serializer=CheckClassScheduleSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            class_schedule = user.class_schedule
            if not class_schedule:
                # 返回空的课程表
                class_schedule = []
            # 返回课程表
            return Response(class_schedule, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

class RecommendLocation(APIView):
    def convert_schedule(self, class_schedule: list):
        converted_schedule = []
        location2time = defaultdict(list)
        for course in class_schedule:
            location = course['location']
            day = course['day']
            section = course['section']
            time = f"{day2num[day]}-{section2num[section]}"
            converted_schedule.append({
                'location': location,
                'time': time
            })
            location2time[location].append(time)
        return converted_schedule, location2time

    def deduplicate_schedule(selg, schedule: list):
        """
        Deduplicate a list of dictionaries by removing identical dictionaries.
        """
        seen = set()
        deduplicated_schedule = []
        
        for class_ in schedule:
            class_tuple = tuple(class_.items())
            if class_tuple not in seen:
                seen.add(class_tuple)
                deduplicated_schedule.append(class_)
        
        return deduplicated_schedule
    
    def get(self, request, *args, **kwargs):
        serializer = RecommendLocationSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            seller_user = serializer.validated_data.get('seller_user')
            buyer_user = serializer.validated_data.get('buyer_user')
            try:
                seller_class_schedule = seller_user.class_schedule
            except:
                return Response({"message": "Seller's class schedule not found"}, status=status.HTTP_404_NOT_FOUND)
            try:
                buyer_class_schedule = buyer_user.class_schedule
            except:
                return Response({"message": "Buyer's class schedule not found"}, status=status.HTTP_404_NOT_FOUND)
            if(not seller_class_schedule or not buyer_class_schedule):
                return Response({"message": "Class schedule not found"}, status=status.HTTP_404_NOT_FOUND)
            seller_class_schedule, seller_location2time = self.convert_schedule(seller_class_schedule)
            buyer_class_schedule, buyer_location2time = self.convert_schedule(buyer_class_schedule)
            # same location and same time
            seller_tuples = {tuple(sorted(d.items())) for d in seller_class_schedule}
            buyer_tuples = {tuple(sorted(d.items())) for d in buyer_class_schedule}
            intersection_class_schedule = [dict(t) for t in seller_tuples & buyer_tuples]
            for class_ in intersection_class_schedule:
                cur_time = class_['time']
                num_day, num_section = cur_time.split('-')
                num_day = int(num_day)
                num_section = int(num_section)
                new_time = f"{num2day[num_day]}{num2section[num_section]}"
                class_['time'] = new_time
            # consider same location but nearby time
            same_locations = list(set(seller_location2time.keys()) & set(buyer_location2time.keys()))
            for location in same_locations:
                seller_time = seller_location2time[location]
                buyer_time = buyer_location2time[location]
                # check nearby, example: 3-1 and 3-2 are nearby
                for seller in seller_time:
                    for buyer in buyer_time:
                        if seller[0] == buyer[0] and [int(seller[0]), int(seller[-1])] in nearby_time:
                            intersection_class_schedule.append({
                                'location': location,
                                'time': f"{num2day[int(seller[0])]}{num2section[min(int(seller[-1]), int(buyer[-1]))]}"
                            })
            # deduplicate the intersection_class_schedule
            intersection_class_schedule = self.deduplicate_schedule(intersection_class_schedule)
            return Response(intersection_class_schedule, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
class UpdatePurchase(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UpdatePurchaseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            raiser = serializer.validated_data.get('raiser')
            item = serializer.validated_data.get('item')
            ## original_purchase查找当前item，seller和buyer相同的对象
            original_purchase = Purchase.objects.filter(
                item=serializer.validated_data.get('item'),
                seller=serializer.validated_data.get('seller'),
                buyer=serializer.validated_data.get('buyer')
            ).first()
            original_raiser = original_purchase.raiser if original_purchase else None
            if item.sold:
                return Response({"message": "This item has already been sold"}, 
                            status=status.HTTP_400_BAD_REQUEST)
            if not original_purchase :
                purchase = serializer.save()
            elif original_raiser == raiser:
                # 如果原有raiser和当前raiser相同，更新purchase
                purchase = serializer.update(original_purchase, serializer.validated_data)
            else:
                # 如果原有raiser和当前raiser不同，返回401
                return Response({"message": "You do not have permission to modify this purchase"}, 
                                status=status.HTTP_401_UNAUTHORIZED)
            return Response({"message": "Purchase updated successfully"}, 
                            status=status.HTTP_200_OK)
        # Check for the specific validation error related to the item not found
        # UpdatePurchase 视图中
        # 检查是否存在 item_not_found 错误代码
        non_field_errors = serializer.errors.get('non_field_errors', [])
        for error in non_field_errors:
            if getattr(error, 'code', None) == 'item_not_found':
                return Response({'detail': 'Item does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoadPurchase(APIView):
    def get(self, request, *args, **kwargs):
        serializer = LoadPurchaseSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            seller = serializer.validated_data.get('seller')
            buyer = serializer.validated_data.get('buyer')
            checker = serializer.validated_data.get('checker')
            item = serializer.validated_data.get('item')
            purchase = Purchase.objects.filter(
                item=item,
                seller=seller,
                buyer=buyer
            ).first()
            if not purchase:
                return Response({"message": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)
            
            original_raiser = purchase.raiser
            sold = item.sold
            if purchase.checked and purchase.checked_at and purchase.results == 0: ## 如果已经被对方查看过了且未决定
                if checker==buyer and (timezone.now() - purchase.checked_at).total_seconds() > 30: ## 若当卖方看到确实是否同意的框之后，买方在超时后调用这个api，则直接设定为拒绝
                    purchase.results = 2
                    purchase.save()
                if checker==seller and (timezone.now() - purchase.checked_at).total_seconds() > 30:  ## 若卖方看到确实是否同意的框之后，卖方在超时后调用这个api，则直接设定为拒绝
                    purchase.results = 2
                    purchase.save()
            if original_raiser!=checker and purchase.checked == True: ##对方(卖家)第二次请求查看时直接返回404
                data = []
                data.append({
                    'price': purchase.price,  # 使用点符号而不是字典索引
                    'time': purchase.time,    # 使用点符号而不是字典索引
                    'place': purchase.place,  # 使用点符号而不是字典索引
                    'room_sold': purchase.room_sold,  # 使用点符号而不是字典索引
                    'sold': sold,
                    'results': purchase.results,  # 使用点符号而不是字典索引
                })
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            if original_raiser!=checker and purchase.checked == False:  ##对方(卖家)第一次请求查看时记录为已读
                purchase.checked = True
                purchase.checked_at = timezone.now()
                purchase.save()
            if original_raiser==checker and purchase.results == 0 : ## 当卖家没有决定是否同意请求时，自己(买家)直接返回404
                return Response({"message": "You do not need to check this purchase"}, 
                                status=status.HTTP_404_NOT_FOUND)
                
            if original_raiser==checker and purchase.buyer_checked==True: ## 当卖家已经返回请求时，自己(买家)第二次查看直接返回404
                data = []
                data.append({
                    'price': purchase.price,  # 使用点符号而不是字典索引
                    'time': purchase.time,    # 使用点符号而不是字典索引
                    'place': purchase.place,  # 使用点符号而不是字典索引
                    'room_sold': purchase.room_sold,  # 使用点符号而不是字典索引
                    'sold': sold,
                    'results': purchase.results,  # 使用点符号而不是字典索引
                })
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            if original_raiser==checker and purchase.results != 0 and purchase.buyer_checked==False: ## 当卖家已经返回请求时，自己(买家)第一次
                purchase.buyer_checked = True
                purchase.save()
            
            data = []
            data.append({
                'price': purchase.price,  # 使用点符号而不是字典索引
                'time': purchase.time,    # 使用点符号而不是字典索引
                'place': purchase.place,  # 使用点符号而不是字典索引
                'room_sold': purchase.room_sold,  # 使用点符号而不是字典索引
                'sold': sold,
                'results': purchase.results,  # 使用点符号而不是字典索引
            })
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ConfirmPurchase(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ConfirmPurchaseSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            confirm = serializer.validated_data.get('confirm')
            item = serializer.validated_data.get('item')
            seller = serializer.validated_data.get('seller')
            buyer = serializer.validated_data.get('buyer')
            purchase = Purchase.objects.filter(
                item=item,
                seller=seller,
                buyer=buyer
            ).first()
            if not purchase:
                return Response({"message": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)
            current_time = timezone.now()
            if confirm and purchase.checked and purchase.checked_at and (current_time - purchase.checked_at).total_seconds() <30:
                purchase.room_sold = True
                purchase.results = 1
                purchase.save()
                if item:
                    item.sold = True
                    item.save()
                return Response({
                    "message": "Purchase confirmed successfully and item has been marked as sold"
                }, status=status.HTTP_200_OK)
            else:
                purchase.results = 2
                purchase.save()
            return Response({"message": "Purchase declined"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
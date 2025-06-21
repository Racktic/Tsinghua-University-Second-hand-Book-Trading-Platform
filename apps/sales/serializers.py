from rest_framework import serializers
from apps.sales.models import Item, Need, Purchase
from apps.accounts.models import User
from .config import LocationOptions

def verify_user_exist(id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise serializers.ValidationError({'non_field_errors': ['User does not exist']})
    return user
def verify_user_is_exist(email,request):
    if not User.objects.filter(email=email).exists():
        raise serializers.ValidationError({'non_field_errors': ['User does not exist']})
    return User.objects.get(email=email)

def verify_user_is_online(email, request):
    user = request.user
    if not user.is_authenticated:
        raise serializers.ValidationError({'non_field_errors': ['User is not logged in']})
    if email and email != user.email:
        raise serializers.ValidationError({'non_field_errors': ['Email mismatch with session user']})
    return user
    
def meta_info_validation(meta_info, required_fields):
    if not meta_info:
        raise serializers.ValidationError({'meta_info': ['meta_info is required.']})
    # 验证 meta_info 的结构
    for field, field_type in required_fields.items():
        if field not in meta_info:
            raise serializers.ValidationError({'meta_info': [f"'{field}' is required in meta_info."]})
        if not isinstance(meta_info[field], field_type):
            raise serializers.ValidationError({'meta_info': [f"'{field}' must be of type {field_type.__name__}."]})
def price_validation(price_lower_bound, price_upper_bound):
    max_price = 999999.99
    if price_lower_bound < 0 or price_lower_bound > max_price:
        raise serializers.ValidationError({'price_lower_bound': ['price_lower_bound must be between 0 and 999999.99']})
    if price_upper_bound < 0 or price_upper_bound > max_price:
        raise serializers.ValidationError({'price_upper_bound': ['price_upper_bound must be between 0 and 999999.99']})
    if price_upper_bound < price_lower_bound:
        raise serializers.ValidationError({'price_upper_bound': ['price_upper_bound cannot be less than price_lower_bound']})
def round_price(data):
    """
    Round the price_lower_bound and price_upper_bound to two decimal places.
    """
    if 'price_lower_bound' in data:
        data['price_lower_bound'] = round(data['price_lower_bound'], 2)
    if 'price_upper_bound' in data:
        data['price_upper_bound'] = round(data['price_upper_bound'], 2)
    return data
class UploadItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('title', 'username', 'price_lower_bound', 'price_upper_bound', 'meta_info', 'picture')  ##name是书籍名称
    
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')           # 仍然收，但只拿来校验一致性
        data['user'] = verify_user_is_online(email, request)
        meta_info = data.get('meta_info')
        if not meta_info:
            raise serializers.ValidationError({'meta_info': ['meta_info is required.']})
        # 验证 meta_info 的结构
        required_fields = {
            'author': str,
            'course': str,
            'teacher': str,
            'description': str,
            'new': int,
        }
        meta_info_validation(meta_info, required_fields)
        data = round_price(data)  # 确保价格字段被正确处理
        price_lower_bound = data.get('price_lower_bound')
        price_upper_bound = data.get('price_upper_bound')
        price_validation(price_lower_bound, price_upper_bound)
        new = meta_info.get('new', 0)
        if not isinstance(new, int) or (new < 0 or new > 10):
            raise serializers.ValidationError({'meta_info': ['new must be an integer between 0 and 10.']})
        return data
    
    def create(self, validated_data):
        item = Item.objects.create(
            title=validated_data['title'],  # 书籍名称
            username=validated_data['username'], # 用户名
            price_lower_bound=validated_data['price_lower_bound'],
            price_upper_bound=validated_data['price_upper_bound'],
            user=validated_data['user'],
            meta_info=validated_data['meta_info'], ## 内部包含author, course, teacher, description, new
            picture=validated_data['picture'],
        )
        return item
    
class SearchItemsSerializer(serializers.Serializer):
    content_type = serializers.CharField(required=True)
    search_keyword = serializers.CharField(required=True, allow_blank=True)
    def validate(self, data):
        content_type = data.get('content_type')
        search_keyword = data.get('search_keyword')
        valid_content_types = ['title', 'course', 'teacher', 'author', 'username', 'description', 'id', 'user_items', 'homepage']
        if content_type not in valid_content_types:
            raise serializers.ValidationError(
                {'content_type': f'Invalid content_type. Must be one of: {", ".join(valid_content_types)}'}
            )

        # 如果 search_keyword 为空，返回所有书目
        
        if(content_type == 'homepage'):  ## 请求首页的时候返回推荐的item
            data['search_all'] = True
            if not search_keyword:
                data['user'] = None
            else:
                data['user'] = verify_user_is_online(search_keyword, self.context.get('request'))
        elif content_type == 'user_items':  ## 请求用户的item
            user= verify_user_is_online(search_keyword, self.context.get('request'))
        elif not search_keyword:       ## 正常搜索的时候也允许空字符串输出，此时返回推荐的item
            data['search_all'] = True 
            data['user'] = None
        else:
            data['search_all'] = False  ## 其余不推荐
        return data

class ModifyItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'title', 'username', 'price_lower_bound', 'price_upper_bound', 'meta_info', 'picture') 
        read_only_fields = ('id',) 
    def validate(self, data):
        request = self.context.get('request')
        if request and 'id' in request.data:
            data['id'] = request.data['id']

        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        meta_info = data.get('meta_info')
        if not meta_info:
            raise serializers.ValidationError({'meta_info': ['meta_info is required.']})
        # 验证 meta_info 的结构
        required_fields = {
            'author': str,
            'course': str,
            'teacher': str,
            'description': str,
            'new': int,
        }
        meta_info_validation(meta_info, required_fields)
        data = round_price(data)  # 确保价格字段被正确处理
        ## 验证价格
        price_lower_bound = data.get('price_lower_bound')
        price_upper_bound = data.get('price_upper_bound')
        price_validation(price_lower_bound, price_upper_bound)
        new = meta_info.get('new', 0)
        if not isinstance(new, int) or (new < 0 or new > 10):
            raise serializers.ValidationError({'meta_info': ['new must be an integer between 0 and 10.']})

        return data
    
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.username = validated_data.get('username', instance.username)
        instance.price_lower_bound = validated_data.get('price_lower_bound', instance.price_lower_bound)
        instance.price_upper_bound = validated_data.get('price_upper_bound', instance.price_upper_bound)
        instance.meta_info = validated_data.get('meta_info', instance.meta_info)
        ## if picture is None, do not update
        if 'picture' in validated_data and validated_data['picture'] is not None:
            instance.picture = validated_data['picture']
        instance.save()
        return instance


class DeleteItemsSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    username = serializers.EmailField(required=True)
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        user= verify_user_is_online(email, request)
        data['user'] = user
        item_id = data.get('id')
        item = Item.objects.filter(id=item_id).first()
        ## 如果item不是这个user发布的
        if item and item.user != user:
            raise serializers.ValidationError({'non_field_errors': ['You do not have permission to delete this item.']})
        if not item:
            raise serializers.ValidationError({'non_field_errors': ['Item does not exist.']})
        data['item'] = item
        return data
    
class RaiseNeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Need
        fields = ('title', 'username', 'price_lower_bound', 'price_upper_bound', 'meta_info')
    
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        meta_info = data.get('meta_info')
        required_fields = {
            'author': str,
            'course': str,
            'teacher': str,
        }
        meta_info_validation(meta_info, required_fields)
        data = round_price(data)  # 确保价格字段被正确处理
        # 验证价格
        price_lower_bound = data.get('price_lower_bound')
        price_upper_bound = data.get('price_upper_bound')
        price_validation(price_lower_bound, price_upper_bound)
        # 如果meta_info里有new字段，验证其类型
        new = meta_info.get('new')
        if new is not None:
            if not isinstance(new, int) or (new < 0 or new > 10):
                raise serializers.ValidationError({'meta_info': ['new must be an integer between 0 and 10.']})
        return data

    def create(self, validated_data):
        user = validated_data.pop('user')
        need = Need.objects.create(
            title=validated_data['title'],
            username=validated_data['username'],
            price_lower_bound=validated_data['price_lower_bound'],
            price_upper_bound=validated_data['price_upper_bound'],
            user=user,
            meta_info=validated_data['meta_info'],
        )
        return need
    

class CheckNeedSerializer(serializers.Serializer):
    username = serializers.EmailField(required=True)
    
    def validate(self, data):
        # 从上下文中获取 request 对象
        request = self.context['request']
        if not request:
            raise serializers.ValidationError({'non_field_errors': ['Invalid request object']})
        
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        return data
        

class ModifyNeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Need
        fields = ('id', 'title', 'username', 'price_lower_bound', 'price_upper_bound', 'meta_info') 
        read_only_fields = ('id',) 
    
    def validate(self, data):
        request = self.context['request']
        if request and 'id' in request.data:
            data['id'] = request.data['id']
        request = self.context['request']
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        required_fields = {
            'author': str,
            'course': str,
            'teacher': str,
        }
        meta_info = data.get('meta_info')
        if not meta_info:
            raise serializers.ValidationError({'meta_info': ['meta_info is required.']})
        meta_info_validation(meta_info, required_fields)
        data = round_price(data)  # 确保价格字段被正确处理
        # 验证价格
        price_lower_bound = data.get('price_lower_bound')
        price_upper_bound = data.get('price_upper_bound')
        price_validation(price_lower_bound, price_upper_bound)
        # 如果meta_info里有new字段，验证其类型
        new = meta_info.get('new')
        if new is not None:
            if not isinstance(new, int) or (new < 0 or new > 10):
                raise serializers.ValidationError({'meta_info': ['new must be an integer between 0 and 10.']})
        return data
    
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.username = validated_data.get('username', instance.username)
        instance.price_lower_bound = validated_data.get('price_lower_bound', instance.price_lower_bound)
        instance.price_upper_bound = validated_data.get('price_upper_bound', instance.price_upper_bound)
        instance.meta_info = validated_data.get('meta_info', instance.meta_info)
        instance.save()
        return instance

class GetNeedSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)  # 添加 id 字段

    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        if request and 'id' in request.query_params:
            data['id'] = request.query_params['id']
        return data

class DeleteNeedSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    username = serializers.EmailField(required=True)
    
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        user = verify_user_is_online(email, request)
        data['user'] = user
        need_id = data.get('id')
        need = Need.objects.filter(id=need_id).first()
        ## 如果item不是这个user发布的
        if need and need.user != user:
            raise serializers.ValidationError({'non_field_errors': ['You do not have permission to delete this need.']})
        if not need:
            raise serializers.ValidationError({'non_field_errors': ['Need does not exist.']})
        data['need'] = need
        return data

class UploadClassScheduleSerializer(serializers.Serializer):
    # the class schedule is an .xls file, which contains the class schedule of a user
    username = serializers.EmailField(required=True)
    class_schedule = serializers.FileField(required=True)
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        # validate if the file is an valid .xls file
        file = data.get('class_schedule')
        if not file.name.endswith('.xls'):
            raise serializers.ValidationError('File must be an .xls file')
        if file.content_type != 'application/vnd.ms-excel':
            raise serializers.ValidationError('Invalid file type. Expected .xls Excel file.')
        
        # validation successful, return data
        return data
    
    def extract_class_schedule(self, file):
        '''
        input: the .xls file which is the class schedule of a user
        output: a list of dicts, each dict contains the 
                course name, teacher, location, day, and section
        '''
        import pandas as pd
        import xlrd

        df = pd.read_excel(file, header=None)
        days = df.iloc[1, 1:].tolist()
        sections = df.iloc[1:, 0].tolist()
        course_list = []
        extraction_fail_flag = False
        for i, section in enumerate(sections[1:]):
            if extraction_fail_flag:
                break
            for j, day in enumerate(days):
                if extraction_fail_flag:
                    break
                try:
                    cell = df.iat[i + 2, j + 1]
                    if pd.notna(cell):
                        for course in str(cell).split('\n'):
                            if course.strip():  # skip empty lines
                                try:
                                    course_name = course.split('(')[0].strip()
                                    teacher_name = course.split('(')[1].split('；')[0].strip()
                                    location = course.split('；')[-1].split(')')[0].strip()
                                    if location == '全周':
                                        continue
                                    else:
                                        find_flag = False
                                        for location_option in LocationOptions:
                                            if location_option in location:
                                                location = location_option
                                                find_flag = True
                                                break
                                        if not find_flag:
                                            continue
                                    course_list.append({
                                        "course": course_name,
                                        "teacher": teacher_name,
                                        "location": location,
                                        "day": str(day).strip(),
                                        "section": str(section).strip(),
                                    })
                                except (IndexError, ValueError):
                                    # Handle cases where the expected format is not met
                                    extraction_fail_flag = True
                                    break

                except (IndexError, ValueError):
                    # print(f"warning: error in cell at section {section}, day {day}")
                    extraction_fail_flag = True
                    break
            
        return course_list, extraction_fail_flag

    def create(self, validated_data):
        # extract info from the .xls file to a json format
        class_schedule_file = validated_data['class_schedule']
        class_schedule_list, extraction_fail_flag = self.extract_class_schedule(class_schedule_file)
        if extraction_fail_flag:
            raise serializers.ValidationError('Error in extracting class schedule. Please check the file format.')
        # then add the list to the corresponding user
        user = User.objects.get(email=validated_data['username'])
        user.class_schedule = class_schedule_list
        user.save()

        return user

class UploadClassScheduleDictSerializer(serializers.Serializer):
    # the class schedule is a dict, which contains the class schedule of a user
    email = serializers.EmailField(required=True)
    courses = serializers.JSONField(required=True)
    
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        data['courses'] = data.get('courses')
        return data
    
    def create(self, validated_data):
        user = validated_data['user']
        courses = validated_data['courses']
        user.class_schedule = courses
        user.save()
        return user

class CheckClassScheduleSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    def validate(self, data):
        request = self.context['request']
        email = data.get('username')
        data['user'] = verify_user_is_online(email, request)
        return data

class RecommendLocationSerializer(serializers.Serializer):
    seller_email = serializers.EmailField(required=True)
    buyer_email = serializers.EmailField(required=True)
    
    def validate(self, data):
        request = self.context.get('request')
        seller_email = data.get('seller_email')
        buyer_email = data.get('buyer_email')
        seller_user = verify_user_is_exist(seller_email, request)
        buyer_user = verify_user_is_exist(buyer_email, request)
        data['seller_user'] = seller_user
        data['buyer_user'] = buyer_user
        return data
    
class UpdatePurchaseSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(required=True)
    seller_id = serializers.IntegerField(required=True)
    buyer_id = serializers.IntegerField(required=True)
    raiser_id = serializers.IntegerField(required=True)
    class Meta:
        model = Purchase
        fields = ('item_id', 'price', 'place', 'time', 'seller_id', 'buyer_id', 'raiser_id')
        
    def validate(self, data):
        request = self.context['request']
        data['raiser'] = verify_user_is_online(None, request)
        item_id = data.get('item_id')
        seller_id = data.get('seller_id')
        buyer_id = data.get('buyer_id')
        item = Item.objects.filter(id=item_id).first()
        if not item:
            raise serializers.ValidationError({'non_field_errors': ['Item does not exist.']}, code='item_not_found')
        if item.user.id != seller_id:
            print(item.user.id, seller_id)
            raise serializers.ValidationError({'non_field_errors': ['Seller does not match the item.']})
        seller = User.objects.filter(id=seller_id).first()
        buyer = User.objects.filter(id=buyer_id).first()
        raiser = data['raiser']
        if raiser != buyer:
            raise serializers.ValidationError({'non_field_errors': ['Raiser must be the buyer.']})
        price = data.get('price')
        if price < 0:
            raise serializers.ValidationError({'price': ['Price must be a non-negative number.']})
        data['price'] = round(price, 2)
        data['item'] = item
        data['seller'] = seller
        data['buyer'] = buyer
        data['raiser'] = raiser
        verify_user_is_online(raiser.email, request)
        return data
    
    def create(self, validated_data):
        item = validated_data['item']
        seller = validated_data['seller']
        buyer = validated_data['buyer']
        raiser = validated_data['raiser']
        purchase = Purchase.objects.create(
            item=item,
            seller=seller,
            buyer=buyer,
            raiser=raiser,
            price=validated_data['price'],
            place=validated_data['place'],
            time=validated_data['time'],
            checked_at=None,
        )
        return purchase
    
    def update(self, instance, validated_data):
        # 更新 Purchase 实例的字段
        instance.item = validated_data.get('item', instance.item)
        instance.seller = validated_data.get('seller', instance.seller)
        instance.buyer = validated_data.get('buyer', instance.buyer)
        instance.raiser = validated_data.get('raiser', instance.raiser)
        instance.price = validated_data.get('price', instance.price)
        instance.place = validated_data.get('place', instance.place)
        instance.time = validated_data.get('time', instance.time)

        instance.checked = False
        instance.buyer_checked = False
        instance.checked_at = None
        instance.room_sold = False
        instance.results = 0

        instance.save()
        return instance
    
class LoadPurchaseSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(required=True)
    seller_id = serializers.IntegerField(required=True)
    buyer_id = serializers.IntegerField(required=True)
    checker_id = serializers.IntegerField(required=True)
    def validate(self, data):
        request = self.context['request']
        data['checker'] = verify_user_is_online(None, request)
        seller_id = data.get('seller_id')
        buyer_id = data.get('buyer_id')
        item_id = data.get('item_id')
        item = Item.objects.filter(id=item_id).first()
        if not item:
            raise serializers.ValidationError({'non_field_errors': ['Item does not exist.']})
        checker = data.get('checker')
        seller = verify_user_exist(seller_id)
        buyer = verify_user_exist(buyer_id)
        if seller == buyer:
            raise serializers.ValidationError({'non_field_errors': ['Seller and buyer cannot be the same.']})
        if checker != seller and checker != buyer:
            raise serializers.ValidationError({'non_field_errors': ['Checker must be either the seller or the buyer.']})
        data['seller'] = seller
        data['buyer'] = buyer
        data['item'] = item
        return data
    
class ConfirmPurchaseSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(required=True)
    responder_id = serializers.IntegerField(required=True)
    seller_id = serializers.IntegerField(required=True)
    buyer_id = serializers.IntegerField(required=True)
    confirm = serializers.BooleanField(required=True)
    def validate(self, data):
        request = self.context['request']
        data['responder'] = verify_user_is_online(None, request)
        seller_id = data.get('seller_id')
        buyer_id = data.get('buyer_id')
        item_id = data.get('item_id')
        item = Item.objects.filter(id=item_id).first()
        if not item:
            raise serializers.ValidationError({'non_field_errors': ['Item does not exist.']})
        responder = data.get('responder')
        seller = verify_user_exist(seller_id)
        buyer = verify_user_exist(buyer_id)
        if responder != seller:
            raise serializers.ValidationError({'non_field_errors': ['Responder must be the seller.']})
        if seller == buyer:
            raise serializers.ValidationError({'non_field_errors': ['Seller and buyer cannot be the same.']})
        data['responder'] = responder
        data['seller'] = seller
        data['buyer'] = buyer
        data['item'] = item
        return data
import jieba
from django.db import models
from django.db.models import Q
import os

class ItemManager(models.Manager):
    def filter(self, *args, **kwargs):
        # 提取自定义过滤参数
        content_type = kwargs.pop('content_type', None)
        search_keyword = kwargs.pop('search_keyword', None)
        print("Custom filter called with args:", args, "kwargs:", kwargs)
        # 初步过滤
        query = super().filter(*args, **kwargs)

        # 根据 content_type 和 search_keyword 动态构建查询条件
        if search_keyword:
            words = jieba.lcut(search_keyword)  # 使用 jieba 分词
            stop_words = {"的", "了", "和", "是", "在", "有", "我", "也", "教材", "教程", "入门", "书籍", "课程", "导论"}
            words = [word for word in words if word not in stop_words]  # 去除停用词
            if words:
                search_query = Q()
                for word in words:
                    # 根据 content_type 动态选择字段
                    if content_type == "title":
                        search_query |= Q(title__icontains=word)
                    elif content_type == "course":
                        search_query |= Q(meta_info__course__icontains=word)
                    elif content_type == "teacher":
                        search_query |= Q(meta_info__teacher__icontains=word)
                    elif content_type == "author":
                        search_query |= Q(meta_info__author__icontains=word)
                    elif content_type == "username":
                        search_query |= Q(username__icontains=word)
                    elif content_type == "description":
                        search_query |= Q(meta_info__description__icontains=word)
                    else:
                        # 如果 content_type 未指定或无效，默认搜索 title
                        search_query |= Q(title__icontains=word)

                query = query.filter(search_query)
        return query
    def find_matching_items(self, need):
        """
        根据需求查找匹配的物品
        :param need: Need实例
        :return: 匹配的Item列表
        """
        # 初步筛选价格匹配的物品
        potential_items = super().filter(
            price_lower_bound__lte=need.price_upper_bound,
            price_upper_bound__gte=need.price_lower_bound,
            sold=False  # 只考虑未售出的物品
        ).exclude(user=need.user)
        
        matching_items = []
        
        for item in potential_items:
            # 标题匹配检查（使用分词软匹配）
            title_match = False
            if item.title and need.title:
                # 使用jieba分词处理标题
                item_words = jieba.lcut(item.title)
                need_words = jieba.lcut(need.title)
                
                # 去除停用词
                stop_words = {"的", "了", "和", "是", "在", "有", "我", "也", "教材", "教程", "入门", "书籍", "课程", "导论"}
                item_words = [word.lower() for word in item_words if word not in stop_words]
                need_words = [word.lower() for word in need_words if word not in stop_words]
                
                # 检查词语匹配
                for item_word in item_words:
                    if any(item_word in need_word or need_word in item_word for need_word in need_words):
                        title_match = True
                        break
            
            # 元数据匹配检查
            meta_match = False
            
            if item.meta_info and need.meta_info:
                # teacher硬匹配
                teacher_match = False
                if 'teacher' in item.meta_info and 'teacher' in need.meta_info:
                    if item.meta_info['teacher'] == need.meta_info['teacher']:
                        teacher_match = True
                
                # author硬匹配
                author_match = False
                if 'author' in item.meta_info and 'author' in need.meta_info:
                    if item.meta_info['author'] == need.meta_info['author']:
                        author_match = True
                
                # course软匹配
                course_match = False
                if 'course' in item.meta_info and 'course' in need.meta_info:
                    item_course = item.meta_info['course']
                    need_course = need.meta_info['course']
                    
                    # 使用jieba分词处理课程名
                    item_course_words = jieba.lcut(item_course)
                    need_course_words = jieba.lcut(need_course)

                    # 去除停用词
                    stop_words = {"的", "了", "和", "是", "在", "有", "我", "也", "教材", "教程", "入门", "书籍", "课程", "导论"}
                    item_course_words = [word.lower() for word in item_course_words if word not in stop_words]
                    need_course_words = [word.lower() for word in need_course_words if word not in stop_words]
                    
                    # 检查课程名词语匹配
                    for item_word in item_course_words:
                        if any(item_word in need_word or need_word in item_word for need_word in need_course_words):
                            course_match = True
                            break
                
                # 元数据匹配成功条件：teacher硬匹配 或 author硬匹配 或 course软匹配
                meta_match = teacher_match or author_match or course_match
            # 最终匹配条件：标题匹配 且 元数据匹配
            if title_match and meta_match:
                matching_items.append(item)
        return matching_items
    
class Item(models.Model):
    class Meta:
        app_label = 'sales'
    title = models.CharField(max_length=255) # eg. the name of the product
    username = models.EmailField(max_length=100) # xqx23@mails.tsinghua.edu.cn
    price_lower_bound = models.DecimalField(max_digits=8, decimal_places=2)
    price_upper_bound = models.DecimalField(max_digits=8, decimal_places=2)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='items')
    # we can add key-value pair in meta_info field 
    meta_info = models.JSONField(null=True, blank=True)  # Meta information in JSON format
    # meta_info include author, course, teacher, description, new
    # Image field for item picture
    picture = models.ImageField(upload_to='item_pictures/', null=True, blank=True)  
    # Indicates if the item is sold
    sold = models.BooleanField(default=False)  
    id = models.AutoField(primary_key=True)  

    objects = ItemManager()

    def delete(self, *args, **kwargs):
        # 删除文件系统中的图片
        if self.picture and os.path.isfile(self.picture.path):
            os.remove(self.picture.path)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return self.title

class NeedManager(models.Manager):
    def find_matching_needs(self, item):
        """
        根据item查找匹配的需求
        :param item: Item实例
        :return: 匹配的Need列表
        """
        # 初步筛选价格匹配的需求,要保证不是自己的需求
        potential_needs = super().filter(
            price_lower_bound__lte=item.price_upper_bound,
            price_upper_bound__gte=item.price_lower_bound,
            is_fulfilled=False  # 只考虑未满足的需求
        ).exclude(user=item.user)
        
        matching_needs = []
        
        for need in potential_needs:
            # 标题匹配检查（使用分词软匹配）
            title_match = False
            if item.title and need.title:
                # 使用jieba分词处理标题
                item_words = jieba.lcut(item.title)
                need_words = jieba.lcut(need.title)
                
                # 去除停用词
                stop_words = {"的", "了", "和", "是", "在", "有", "我", "也", "教材", "教程", "入门", "书籍", "课程", "导论"}
                item_words = [word.lower() for word in item_words if word not in stop_words]
                need_words = [word.lower() for word in need_words if word not in stop_words]
                
                # 检查词语匹配
                for item_word in item_words:
                    if any(item_word in need_word or need_word in item_word for need_word in need_words):
                        title_match = True
                        break
            
            # 元数据匹配检查
            meta_match = False
            
            if item.meta_info and need.meta_info:
                # teacher硬匹配
                teacher_match = False
                if 'teacher' in item.meta_info and 'teacher' in need.meta_info:
                    if item.meta_info['teacher'] == need.meta_info['teacher']:
                        teacher_match = True
                
                # author硬匹配
                author_match = False
                if 'author' in item.meta_info and 'author' in need.meta_info:
                    if item.meta_info['author'] == need.meta_info['author']:
                        author_match = True
                
                # course软匹配
                course_match = False
                if 'course' in item.meta_info and 'course' in need.meta_info:
                    item_course = item.meta_info['course']
                    need_course = need.meta_info['course']
                    
                    # 使用jieba分词处理课程名
                    item_course_words = jieba.lcut(item_course)
                    need_course_words = jieba.lcut(need_course)

                    # 去除停用词
                    item_course_words = [word.lower() for word in item_course_words if word not in stop_words]
                    need_course_words = [word.lower() for word in need_course_words if word not in stop_words]
                    
                    # 检查课程名词语匹配
                    for item_word in item_course_words:
                        if any(item_word in need_word or need_word in item_word for need_word in need_course_words):
                            course_match = True
                            break
                
                # 元数据匹配成功条件：teacher硬匹配 或 author硬匹配 或 course软匹配
                meta_match = teacher_match or author_match or course_match
            
            # 最终匹配条件：标题匹配 且 元数据匹配
            if title_match and meta_match:
                matching_needs.append(need)
        
        return matching_needs

class Need(models.Model):
    class Meta:
        app_label = 'sales'
    title = models.CharField(max_length=255) # eg. the name of the item
    username = models.EmailField(max_length=100)
    price_lower_bound = models.DecimalField(max_digits=8, decimal_places=2)
    price_upper_bound = models.DecimalField(max_digits=8, decimal_places=2)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='needs')
    meta_info = models.JSONField(null=True, blank=True)  # Meta information include author, course, teacher, new
    is_fulfilled = models.BooleanField(default=False)  # Indicates if the need is fulfilled
    id = models.AutoField(primary_key=True)

    objects = NeedManager()

    def __str__(self):
        return self.title

class Purchase(models.Model):
    class Meta:
        app_label = 'sales'
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sales')
    buyer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='purchases')
    raiser = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='raiser')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    time = models.CharField(max_length=255)  # Time of purchase
    place = models.CharField(max_length=255)  # Place of purchase
    checked = models.BooleanField(default=False)  # Indicates if the purchase has been checked by the seller
    buyer_checked = models.BooleanField(default=False)  # Indicates if the result of the purchase has been checked by the buyer
    checked_at = models.DateTimeField(null=True, blank=True)  # Time when the purchase was checked
    room_sold = models.BooleanField(default=False)  # Indicates if the item has been sold in this chat room
    results = models.IntegerField(default=0)  # =0 not checked, =1 conformed, =2 declined
    id = models.AutoField(primary_key=True)
    

    def __str__(self):
        return f"Purchase of {self.item.title} by {self.buyer.username} from {self.seller.username}"

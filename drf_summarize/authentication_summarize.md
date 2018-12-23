# drf 认证总结及源码
## 一. 认证执行逻辑
### 1. 自定义认证类
![avatar](./pictures/authentication/1.png)
### 2. CBV视图类指定认证类
![avatar](./pictures/authentication/2.png)
### 3. 在Django setting.py中设置全局认证类
![avatar](./pictures/authentication/3.png)
### 4. 在Django的路由中配置路由urls.py
![avatar](./pictures/authentication/4.png)
### 5. 执行顺序
1 当有...api/v1/order/get?token=....请求时。  
2 先进行路由匹配执行匹配到的视图类OrderView的as_view()方法  
3 由于OrderView中没有as_view()方法，则执行其父类APIView中的as_view()方法  
![avatar](./pictures/authentication/5.png)
APIView.as_view()方法
![avatar](./pictures/authentication/6.png)  
4 在执行APIView父类View中的as_view()方法时执行了dispatch()方法。View是Django中的类(from django.views import View)  
![avatar](./pictures/authentication/7.png)
5 由于APIView中复写了dispatch()方法那么执行APIView中的dispatch方法  
6 request = self.initialize_request(request, *args, **kwargs)将Django原生的request封装成drf的request  
![avatar](./pictures/authentication/8.png)  
7 获取authentication_classes = [...] 中认证类的实例对象并作为参数传入Request  
都是APIView类中的方法
![avatar](./pictures/authentication/10.png)
![avatar](./pictures/authentication/9.png)  
8 在APIView dispatch中self.initial(request, *args, **kwargs)  
![avatar](./pictures/authentication/11.png)
![avatar](./pictures/authentication/12.png)  
9 执行request.py中Request实例对象中的user方法  
![avatar](./pictures/authentication/13.png)  
![avatar](./pictures/authentication/14.png)
![avatar](./pictures/authentication/15.png)
## 二. 认证总结
```
(1)创建认证类
继承BaseAuthentication    --->>1.重写authenticate方法；2.authenticate_header方法直接写pass就可以（这个方法必须写）
(2)authenticate()返回值（三种）
None ----->>>当前认证不管，等下一个认证来执行
raise exceptions.AuthenticationFailed('用户认证失败')       # from rest_framework import exceptions
有返回值元祖形式：（元素1，元素2）      #元素1复制给request.user;  元素2复制给request.auth
(3)局部使用
authentication_classes = [BaseAuthentication,]
(4)全局使用
在django的settings.py文件中配置
# 设置全局认证
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES":['API.utils.auth.Authentication',]
}
```










## 运行项目注意事项

静态服务器：http://linfaner.top:8080/
动态服务器：http://linfaner.top:8000/

#### 1、redis的ip和端口需要配置，并且确定启动redis


#### 2、将模型类拷贝
#### 3、迁移建表

#### 4、将数据库备份sql脚本放在script目录下面

```python
mysql -h ip地址 -u root -p ihome < ihome.sql
```

#### 5、进入虚拟环境，并且安装requirements.txt
```python
pip install -r requirements.txt
```


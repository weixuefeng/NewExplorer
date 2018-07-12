### Transactions ###
- api_show_client_transactions
```
{
  "docs": [
    {
      "operations": [
        
      ],
      "contract": null,
      "_id": "0xe829a33c3e025c0aa1d81ad99a56be7598ff655feecad99962f167c230e1f48f",
      "blockNumber": 7339862,
      "timeStamp": "1526637504",
      "nonce": 20127,
      "from": "0x003bbce1eac59b406dd0e143e856542df3659075",
      "to": "0x782c7147fbf339660d74f407832e0fecf4d49d31",
      "value": "5000000000000000000",
      "gas": "100000",
      "gasPrice": "14959965017",
      "gasUsed": "21000",
      "input": "0x",
      "error": "",
      "id": "0xe829a33c3e025c0aa1d81ad99a56be7598ff655feecad99962f167c230e1f48f"
    }
  ],
  "total": 1,
  "limit": 50,
  "page": 1,
  "pages": 1
}
```


### 项目准备： ###
（1）、cd到项目目录

（2）、`git clone git@gitlab.newtonproject.org:xiawu/newton-explorer.git` 

（3）、创建虚拟环境：mkvirtualenv explorer  

（4）、进入虚拟环境：workon explorer  

（5）、进入项目目录下的explorer目录下  

（6）、安装项目依赖的包：`pip install -r requirements.txt`  

（7）、安装MySQL、MongoDB、Redis数据库，详见项目newton-documentation/ python-development-guide.md  
需要注意的是MongoDB版本安装3.4版，使用安装命令：brew install mongodb@3.4

需配置~/.bash_profile文件,加入代码:
```
export MONGO_PATH=/usr/local/opt/mongodb@3.4
export PATH=$PATH:$MONGO_PATH/bin
```

（8）、安装grunt-cli:
`brew install grunt-cli`

（9）、由于template.pot文件无法自动转换为po文件，所以需要安装一个grunt-pofriend  
- 首先使用命令安装grunt-pofriend：`npm install grunt-pofriend --save-dev`
- 然后编辑explorer/explorer/templates/ui/Gruntfile.js文件
添加`grunt.loadNpmTasks('grunt-pofriend');`  
在grunt.initConfig中添加：  
```
updatePO: {
    all: {
      files: {
        'po/template.pot': ['po/*.po']
      }
    }
  }
```
更新grunt.registerTask，在其中添加 updatePO  
`grunt.registerTask('translate', ['nggettext_extract', 'updatePO']);`


### 项目setup: ###
（1）、开启MySQL、Redis、MongoDB服务  

（2）、进入项目目录下的explorer目录下  

（3）、使用命令：newtonbd同步数据  

（4）、make 编译项目  

（5）、如果改动文字样式，需要使用brunt translate编译

（6）、使用命令：./environment/test/testing.sh 启动项目


### 项目文件介绍： ###
locale文件夹：存放国际化功能所需文件，可以指定要翻译的字符串，django根据特定的访
问者偏好设置，进行调用相应的翻译文本。

requirements.txt文件：内容为项目所依赖的环境

package.txt文件：平台系统所用的包

apps文件夹：存放各个应用  
apps/models：数据库表结构  
apps/services：接口文件（用于查询结果）  
apps/view：视图文件  
apps/forms：表单验证文件  
app分为三个等级：
- 应用级（比如注册、登录）
- 基础工具（base、storage存储）
- 基础组件


config文件夹：存放部分配置文件  
注意：explorer/explorer文件夹下的settings.py及相似文件名的文件也为配置文件，其关  
系为settings.py包含setting_local.py包含config中的common_settings.py和  
setting_label.py包含server.py  
注意：经常改动的配置，最好放在config文件夹下的文件中

middlewares文件夹：存放中间件文件  
locale_middleware.py文件：功能为自动判断语言  
timezone_middleware.py文件：功能为自动判断时区  

utils文件夹：存放工具文件

templates文件夹：存放静态文件、css、js

tasks文件夹：同步执行的任务

wsgi.py文件: 内置runserver命令的WSGI应用配置

`__init__.py`文件: 用来告诉python，当前目录是python模块

urls.py文件: URL根配置





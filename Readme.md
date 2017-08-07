牛客网刷题插件
============

临时所写，疏漏较多

原理
------------
1. nowcoder.py

    先对指定题目进行get请求，拿到题目

    再写完之后进行post提交

    再循环get评测结果
    
    需要BeautifulSoup库支持
    
2. nowcoder.el

   运行nowcoder.py将输出导入buffer中进行处理

   再导入一个临时文件进行提交
   
用法
-------------

M-x nowcoder-coding-interviews

    这个是牛客网剑指offer专题，输入第几个题目即可

    C-c C-c 写完之后运行该按键，自动提交并返回结果

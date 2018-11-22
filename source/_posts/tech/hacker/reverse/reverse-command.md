title: 逆向工具
date: 2018-10-20 20:10:33
tags:
  - hacker
  - reverse
layout: post
categories: tech
---

## 逆向工具命令：
- ldd: 依赖链接库查看(mac 参考otool  -L)
- objdump: 依赖libbfd, 提取各种信息
- otool: 解析OS X 二进制文件
- dumpbin: 微软提取pe文件信息
- nm: display name list (symbol table)
- c++filt: C++,java程序重载函数还原(nm test |grep func|c++filt)
- strings: 字符串搜索

- ndisasm|diSorm: 流式反汇编器

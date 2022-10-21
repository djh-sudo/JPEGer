# JPEGer
`JPEG analyser`，` Steganography`，`JPEG format`

## Introduction

`JPEG`文件格式分析，通过`DCT`算法隐藏指定信息到`JPEG`图片中，不依赖于第三方库`opencv`。	示例中隐藏的信息是`src`中的`secret.py`，隐藏载体是`src`文件夹中的`pic.jpg`。

## Details

通过`DCT`系数矩阵的两个块系数的相对大小，存储隐藏信息的一个比特分量。`main.py`中设定的是`(15,16)`这两个块。

## Warning

解析器不完善，标准中的一些情况被忽略了，例如这里只考虑了`YCbCr`全采样下，即`4:4:4`情况下的解析，其它采样率下没有考虑，关于`JPEG`各个块的解析，可以根据需要，自行修改`JPEGer.py`。
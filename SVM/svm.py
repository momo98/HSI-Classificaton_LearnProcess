# -*-coding=utf-8 -*-
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
import numpy as np
import scipy.io as sio
import random
import matplotlib.pyplot as plt
import os

# 导入数据
path = os.path.join("F:\deeplearning\hyperspectral_datasets")  # change this path for your dataset
PaviaU = os.path.join(path,'F:\deeplearning\hyperspectral_datasets\Salinas_corrected.mat')
PaviaU_gt = os.path.join(path,'F:\deeplearning\hyperspectral_datasets\Salinas_gt.mat')
method_path = 'SVM'

# 加载数据，返回值为一个字典内嵌ndarray的数据结构
data = sio.loadmat(PaviaU)
data_gt = sio.loadmat(PaviaU_gt)
im = data['salinas_corrected']  # im为样本点的光谱值的ndarray
imGIS = data_gt['salinas_gt']  # imGIS样本点的标签值组成的ndarray

# 归一化，这个归一化的方法有点不一样
im = (im - float(np.min(im)))
im = im/np.max(im)

# 训练数据集的个数200, deepth为通道数103，classes为类别数
sample_num = 200
deepth = im.shape[2]
classes = np.max(imGIS)

# 定义三个字典，分别为：
data_pos = {}
train_pos = {}
test_pos = {}

# 在三个字典中，放入与类别数目相等的列表
for i in range(1,classes+1):
    data_pos[i]=[]
    train_pos[i]=[]
    test_pos[i] = []

# 遍历所有的标签值，对每一个个标签值进行分类组合，得到{1类：对应点坐标列表，2类：对应的坐标列表，等等}
for i in range(imGIS.shape[0]):
    for j in range(imGIS.shape[1]):
        for k in range(1,classes+1):
            if imGIS[i,j]==k:
                data_pos[k].append([i,j])
                continue

# 取出测试集和训练集
for i in range(1,classes+1):
    # Returns a new list containing elements from the population while
    #         leaving the original population unchanged. 大小为sample_num
    indexies = random.sample(range(len(data_pos[i])),sample_num)
    for k in range(len(data_pos[i])):
        if k not in indexies:
            test_pos[i].append(data_pos[i][k])
        else:
            train_pos[i].append(data_pos[i][k])

train = []
train_label = []
test = []
test_label = []

for i in range(1,len(train_pos)+1):
    for j in range(len(train_pos[i])):
        row,col = train_pos[i][j]
        train.append(im[row,col])
        train_label.append(i)

for i in range(1,len(test_pos)+1):
    for j in range(len(test_pos[i])):
        row,col = test_pos[i][j]
        test.append(im[row,col])
        test_label.append(i)
if not os.path.exists(os.path.join(method_path,'result')):
    os.makedirs(os.path.join(method_path,'result'))


# 处理数据完成，现在开始应用sklearning
clf = SVC(C=100,kernel='rbf',gamma=1)
train = np.asarray(train)
train_label = np.asarray(train_label)
clf.fit(train,train_label)

C = np.max(imGIS)
matrix = np.zeros((C,C))
for i in range(len(test)):
    r = clf.predict(test[i].reshape(-1,len(test[i])))
    matrix[r-1,test_label[i]-1] += 1

ac_list = []
for i in range(len(matrix)):
    ac = matrix[i, i] / sum(matrix[:, i])
    ac_list.append(ac)
    print(i+1,'class:','(', matrix[i, i], '/', sum(matrix[:, i]), ')', ac)
print('confusion matrix:')
print(np.int_(matrix))
print('total right num:', np.sum(np.trace(matrix)))
print('total test num:',np.sum(matrix))
accuracy = np.sum(np.trace(matrix)) / np.sum(matrix)
print('Overall accuracy:', accuracy)
# kappa
kk = 0
for i in range(matrix.shape[0]):
    kk += np.sum(matrix[i]) * np.sum(matrix[:, i])
pe = kk / (np.sum(matrix) * np.sum(matrix))
pa = np.trace(matrix) / np.sum(matrix)
kappa = (pa - pe) / (1 - pe)
ac_list = np.asarray(ac_list)
aa = np.mean(ac_list)
print('Average accuracy:',aa)
print('Kappa:', kappa)
sio.savemat(os.path.join(r'HSI_Classification-master\SVM\result', 'result.mat'), {'oa': accuracy,'aa':aa,'kappa':kappa,'ac_list':ac_list,'matrix':matrix})


# 绘图。是否绘制背景
test_bg = False
iG = np.zeros((imGIS.shape[0],imGIS.shape[1]))
for i in range(imGIS.shape[0]):
    for j in range(imGIS.shape[1]):
        if imGIS[i,j] == 0:
            if test_bg:
                iG[i,j] = (clf.predict(im[i,j].reshape(-1,len(im[i,j]))))
            else:
                iG[i,j]=0
        else:
            iG[i,j] = (clf.predict(im[i,j].reshape(-1,len(im[i,j]))))

if test_bg:
    iG[0,0] = 0

# de_map = iG[::-1]  # 切片，获取从后向前排列的元素
de_map = iG  # 切片，获取从后向前排列的元素
fig, _ = plt.subplots()
height, width = de_map.shape
fig.set_size_inches(width/100.0, height/100.0)
plt.gca().xaxis.set_major_locator(plt.NullLocator())
plt.gca().yaxis.set_major_locator(plt.NullLocator())
plt.subplots_adjust(top=1,bottom=0,left=0,right=1,hspace=0,wspace=0)
plt.axis('off')
plt.axis('equal')
plt.imshow(de_map, cmap='nipy_spectral')
# plt.pcolor(de_map)
plt.savefig(os.path.join(r'HSI_Classification-master\SVM\result', 'decode_map.png'),format='png',dpi=600)#bbox_inches='tight',pad_inches=0)
# plt.close()
plt.show()
print('decode map get finished')

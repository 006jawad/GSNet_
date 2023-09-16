import numpy as np
import matplotlib.pyplot as plt
from skimage.util import montage
import torch
import torch.nn as nn
import warnings
warnings.simplefilter("ignore")


class conv_block_1(nn.Module):
    def __init__(self, ch_in,ch_out):
        super(conv_block_1, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv3d(ch_in, ch_out, kernel_size=3, stride=1,padding=1,bias=True),
            nn.BatchNorm3d(ch_out),
            nn.ReLU(inplace=True),


        )

    def forward(self, x):
        x = self.conv1(x)
        return x


class conv_block_2(nn.Module):
    def __init__(self, ch_in, ch_out):
        super(conv_block_2, self).__init__()
        self.conv2 = nn.Sequential(
            nn.Conv3d(ch_in, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=True),
            nn.BatchNorm3d(ch_out),
            nn.ReLU(inplace=True),

            nn.Conv3d(ch_out, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=True),
            nn.BatchNorm3d(ch_out),
            nn.ReLU(inplace=True),


        )

    def forward(self, x):
        x = self.conv2(x)
        return x


class conv_block_1_with_drop(nn.Module):
    def __init__(self, ch_in, ch_out):
        super(conv_block_1_with_drop, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv3d(ch_in, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=True),
            nn.BatchNorm3d(ch_out),
            nn.Dropout3d(p=0.2),
            nn.ReLU(inplace=True),


        )

    def forward(self, x):
        x = self.conv1(x)
        return x


class conv_block_2_with_drop(nn.Module):
    def __init__(self, ch_in, ch_out):
        super(conv_block_2_with_drop, self).__init__()
        self.conv2 = nn.Sequential(
            nn.Conv3d(ch_in, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=False),
            nn.InstanceNorm3d(ch_out),
            nn.Dropout3d(p=0.2),
            nn.ReLU(inplace=True),

            nn.Conv3d(ch_out, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=False),
            nn.InstanceNorm3d(ch_out),
            nn.Dropout3d(p=0.2),
            nn.ReLU(inplace=True),


        )

    def forward(self, x):
        x = self.conv2(x)
        return x


class up_conv(nn.Module):
    def __init__(self, ch_in, ch_out):
        super(up_conv, self).__init__()
        self.up = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv3d(ch_in, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=False),
            nn.InstanceNorm3d(ch_out),
            nn.ReLU(inplace=True),


        )

    def forward(self, x):
        x = self.up(x)
        return x


class single_conv(nn.Module):
    def __init__(self, ch_in, ch_out):
        super(single_conv, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv3d(ch_in, ch_out, kernel_size=3,
                      stride=1, padding=1, bias=True),
            nn.BatchNorm3d(ch_out),

            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.conv(x)
        return x
class Attention_block(nn.Module):
    def __init__(self, F_g, F_l, F_int):
        super(Attention_block, self).__init__()
        self.W_g = nn.Sequential(
            nn.Conv3d(F_g, F_int, kernel_size=1,
                      stride=1, padding=0, bias=False),
            nn.InstanceNorm3d(F_int)
        )
        self.W_x = nn.Sequential(
            nn.Conv3d(F_l, F_int, kernel_size=1,
                      stride=1, padding=0, bias=False),
            nn.InstanceNorm3d(F_int)
        )
        self.psi = nn.Sequential(
            nn.Conv3d(F_int, 1, kernel_size=1,
                      stride=1, padding=0, bias=False),
            nn.InstanceNorm3d(1),
            nn.Softmax()
        )
        self.relu = nn.ReLU(inplace=True)
    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)
        psi = self.relu(g1+x1)
        psi = self.psi(psi)
        return x*psi
class GSNet(nn.Module):
    def __init__(self, img_ch=4, output_ch=4):
        super(GSNet, self).__init__()
        self.Maxpool = nn.MaxPool3d(kernel_size=2, stride=2)
        self.Conv1 = conv_block_2_with_drop(ch_in=img_ch, ch_out=16)
        self.Conv2 = conv_block_2_with_drop(ch_in=16, ch_out=32)
        self.Conv3 = conv_block_2_with_drop(ch_in=32, ch_out=64)
        self.Conv4 = conv_block_2_with_drop(ch_in=64, ch_out=128)
        self.Conv5 = conv_block_2_with_drop(ch_in=128, ch_out=256)
        self.Up5 = up_conv(ch_in=256, ch_out=128)
        self.Att5 = Attention_block(F_g=128, F_l=128, F_int=64)
        self.Up_conv5 = conv_block_2_with_drop(ch_in=256, ch_out=128)
        self.Up4 = up_conv(ch_in=128, ch_out=64)
        self.Att4 = Attention_block(F_g=64, F_l=64, F_int=32)
        self.Up_conv4 = conv_block_2_with_drop(ch_in=128, ch_out=64)
        self.Up3 = up_conv(ch_in=64, ch_out=32)
        self.Att3 = Attention_block(F_g=32, F_l=32, F_int=16)
        self.Up_conv3 = conv_block_2_with_drop(ch_in=64, ch_out=32)
        self.Up2 = up_conv(ch_in=32, ch_out=16)
        self.Att2 = Attention_block(F_g=16, F_l=16, F_int=8)
        self.Up_conv2 = conv_block_2_with_drop(ch_in=32, ch_out=16)
        self.Conv_1x1 = nn.Conv3d(
            16, output_ch, kernel_size=1, stride=1, padding=0)
    def forward(self, x):
        x1 = self.Conv1(x)
        x2 = self.Maxpool(x1)
        x2 = self.Conv2(x2)
        x3 = self.Maxpool(x2)
        x3 = self.Conv3(x3)
        x4 = self.Maxpool(x3)
        x4 = self.Conv4(x4)
        x5 = self.Maxpool(x4)
        x5 = self.Conv5(x5)
        d5 = self.Up5(x5)
        x4 = self.Att5(g=d5, x=x4)
        d5 = torch.cat((x4, d5), dim=1)
        d5 = self.Up_conv5(d5)
        d4 = self.Up4(d5)
        x3 = self.Att4(g=d4, x=x3)
        d4 = torch.cat((x3, d4), dim=1)
        d4 = self.Up_conv4(d4)
        d3 = self.Up3(d4)
        x2 = self.Att3(g=d3, x=x2)
        d3 = torch.cat((x2, d3), dim=1)
        d3 = self.Up_conv3(d3)
        d2 = self.Up2(d3)
        x1 = self.Att2(g=d2, x=x1)
        d2 = torch.cat((x1, d2), dim=1)
        d2 = self.Up_conv2(d2)
        d1 = self.Conv_1x1(d2)
        return d1

class ShowResult:
    def mask_preprocessing(self, mask):
        mask = mask.squeeze().cpu().detach().numpy()
        mask = np.moveaxis(mask, (0, 1, 2, 3), (0, 3, 2, 1))
        mask_WT = np.rot90(montage(mask[0]))
        mask_TC = np.rot90(montage(mask[1]))
        mask_ET = np.rot90(montage(mask[2]))
        return mask_WT, mask_TC, mask_ET
    def image_preprocessing(self, image):
        image = image.squeeze().cpu().detach().numpy()
        image = np.moveaxis(image, (0, 1, 2, 3), (0, 3, 2, 1))
        flair_img = np.rot90(montage(image[0]))
        return flair_img
    def plot(self, image, prediction,_id):
        image = self.image_preprocessing(image)
        pr_mask_WT, pr_mask_TC, pr_mask_ET = self.mask_preprocessing(prediction)
        _, axes = plt.subplots(figsize = (10, 10))
        axes.axis("off")
        axes.imshow(image, cmap ='bone')
        axes.imshow(np.ma.masked_where(pr_mask_WT == False, pr_mask_WT),
                  cmap='cool_r', alpha=0.6)
        axes.imshow(np.ma.masked_where(pr_mask_TC == False, pr_mask_TC),
                  cmap='YlGnBu', alpha=0.6)
        axes.imshow(np.ma.masked_where(pr_mask_ET == False, pr_mask_ET),
                  cmap='cool', alpha=0.6)
        plt.tight_layout()
        plt.savefig(f'./static/data/{_id}_out.png')
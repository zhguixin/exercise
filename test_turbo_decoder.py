#!/usr/bin/env python
#coding=utf-8

import sys
import wx 
import commands
import subprocess
from wx.lib.pubsub import Publisher
import time
import threading 

# 设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)  
sys.setdefaultencoding("utf-8")

# 测试完成或未尽进行
flag = 0

class MainFrame(wx.Frame):
    def __init__(self, parent,id):
        wx.Frame.__init__(self, parent, id, title=u'测试面板', size=(780,765))
        self.Centre()
        panel = wx.Panel(self)

        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")
        Publisher().subscribe(self.updateDisplay_gauge, "update_gauge")

        # 测试类型
        test_types_list = [u'Turbo码内核测试', u'PDSCH测试']
        test_types_st = wx.StaticText(panel, -1, u'测试类型:')
        self.test_types = wx.ComboBox(panel, -1, test_types_list[0],
            wx.DefaultPosition, wx.DefaultSize, test_types_list, 0)
        self.Bind(wx.EVT_COMBOBOX, self.OnChoose, self.test_types) 

	   # 编码参数		
        block_st = wx.StaticText(panel, -1, u'块大小(bit):')
        self.block_txt = wx.TextCtrl(panel, -1, '400')
        code_rate_list = ['0.1','0.2','0.3','0.4','0.5','0.6','0.7']
        code_rate_st = wx.StaticText(panel, -1, u'编码码率:')
        self.code_rate = wx.ComboBox(panel, -1, code_rate_list[2],
            wx.DefaultPosition, wx.DefaultSize, code_rate_list, 0)
        # 译码参数
        decode_list = ['max-log-map', 'sova', 'log-map']
        decode_st = wx.StaticText(panel, -1, u'译码方法:')
        self.decode_txt = wx.ComboBox(panel, -1, decode_list[0],
            wx.DefaultPosition, wx.DefaultSize, decode_list, 0)
        iterate_list = ['1','2','3','4','5']
        iterate_st = wx.StaticText(panel, -1, u'迭代次数:')
        self.iterate_txt = wx.ComboBox(panel, -1, iterate_list[2],
            wx.DefaultPosition, wx.DefaultSize, iterate_list, 0)
        sova_delta_st = wx.StaticText(panel, -1, u'历史窗口:')
        self.sova_delta_txt = wx.TextCtrl(panel, -1, '30')
        self.sova_fast = wx.CheckBox(panel, -1,label=u'使用SOVA快速算法',
            pos=wx.DefaultPosition, size=wx.DefaultSize)
        # 调制参数
        modulation_list = ['qpsk','16qam','64qam']
        modulation_st = wx.StaticText(panel, -1, u'调制方式:')
        self.modulation_txt = wx.ComboBox(panel, -1, modulation_list[0],
        wx.DefaultPosition, wx.DefaultSize, modulation_list, 0)
        # 解调参数
        judge_list = [u'软判决', u'硬判决']
        judge_st = wx.StaticText(panel, -1, u'判决方式:')
        self.judge_txt = wx.ComboBox(panel, -1, judge_list[0],
            wx.DefaultPosition, wx.DefaultSize, judge_list, 0)
        SNR_st = wx.StaticText(panel, -1, u'比特信噪比(dB):')
        self.SNR_txt = wx.TextCtrl(panel, -1, '2')

        self.test_btn = wx.Button(panel, label="开始测试")
        self.test_btn.SetBackgroundColour('black')
        self.test_btn.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnTest, self.test_btn)      

        self.DisplayText = wx.TextCtrl(panel, -1, '',   
            size=(350, 550), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        self.DisplayText.SetBackgroundColour('gray')   

        self.m_gauge1 = wx.Gauge(panel, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.m_gauge1.SetValue(0) 
        self.m_staticText2 = wx.StaticText(panel, wx.ID_ANY, u'\t\t', wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)        

        # 开始布局
        flexsizer1 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        flexsizer1.AddGrowableCol(1)
        flexsizer1.Add(test_types_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        flexsizer1.Add(self.test_types, 0, wx.EXPAND)

        flexsizer_encode = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        flexsizer_encode.AddGrowableCol(1)
        flexsizer_encode.Add(block_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        flexsizer_encode.Add(self.block_txt, 0, wx.EXPAND)
        flexsizer_encode.Add(code_rate_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        flexsizer_encode.Add(self.code_rate, 0, wx.EXPAND)
        sizer1 = wx.StaticBoxSizer(wx.StaticBox(panel, wx.NewId(), u'编码参数'), wx.VERTICAL)
        sizer1.Add(flexsizer_encode, 0, wx.EXPAND | wx.ALL, 10)

        flexsizer_decode = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        flexsizer_decode.Add(decode_st, 0,wx.ALIGN_CENTER_VERTICAL)
        flexsizer_decode.Add(self.decode_txt, 0, wx.EXPAND)
        flexsizer_decode.Add(iterate_st, 0, wx.ALIGN_CENTER_VERTICAL)
        flexsizer_decode.Add(self.iterate_txt, 0, wx.EXPAND)
        flexsizer_decode.Add(sova_delta_st, 0, wx.ALIGN_CENTER_VERTICAL)
        flexsizer_decode.Add(self.sova_delta_txt, 0, wx.EXPAND)
        sizer2 = wx.StaticBoxSizer(wx.StaticBox(panel, wx.NewId(), u'译码参数'), wx.VERTICAL)
        sizer2.Add(flexsizer_decode, 0, wx.EXPAND | wx.ALL, 10)
        sizer2.Add(self.sova_fast, 0, wx.EXPAND | wx.ALL, 10)

        flexsizer_modulate = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        flexsizer_modulate.Add(modulation_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        flexsizer_modulate.Add(self.modulation_txt, 0, wx.EXPAND)
        sizer3 = wx.StaticBoxSizer(wx.StaticBox(panel, wx.NewId(), u'调制参数'), wx.VERTICAL)
        sizer3.Add(flexsizer_modulate, 0, wx.EXPAND | wx.ALL, 10)

        flexsizer_demodulate = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        flexsizer_demodulate.Add(judge_st, 0, wx.ALIGN_CENTER_VERTICAL)
        flexsizer_demodulate.Add(self.judge_txt, 0, wx.EXPAND)
        sizer4 = wx.StaticBoxSizer(wx.StaticBox(panel, wx.NewId(), u'解调参数'), wx.VERTICAL)
        sizer4.Add(flexsizer_demodulate, 0, wx.EXPAND | wx.ALL, 10)

        flexsizer_channel = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        flexsizer_channel.Add(SNR_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)        
        flexsizer_channel.Add(self.SNR_txt, 0, wx.EXPAND)
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(panel, wx.NewId(), u'信道参数'), wx.VERTICAL)	
        sizer5.Add(flexsizer_channel, 0, wx.EXPAND | wx.ALL, 10)

        flexsizer2 = wx.FlexGridSizer(cols=1, hgap=10, vgap=10)
        flexsizer2.AddGrowableCol(1)
        flexsizer2.Add(sizer1, 0, wx.EXPAND)
        flexsizer2.Add(sizer2, 0, wx.EXPAND)
        flexsizer2.Add(sizer3, 0, wx.EXPAND)
        flexsizer2.Add(sizer4, 0, wx.EXPAND)
        flexsizer2.Add(sizer5, 0, wx.EXPAND)

        box2 = wx.StaticBoxSizer(wx.StaticBox(panel, wx.NewId(), u'测试结果'), wx.VERTICAL)
        box2.Add(self.DisplayText, 0, wx.EXPAND | wx.ALL, 10)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(flexsizer2, 0, wx.EXPAND | wx.ALL)
        hbox1.Add((30,30), 0)
        hbox1.Add(box2, 1, wx.EXPAND | wx.ALL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.m_gauge1, 1, wx.EXPAND | wx.ALL)
        hbox.Add(self.m_staticText2, 0,wx.ALIGN_CENTER)
        # hbox.Add((10,10), 1)
        hbox.Add(self.test_btn, 0,wx.ALIGN_CENTER)
        # hbox.Add((10,10), 0)
        hbox.Add((20,10), 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(flexsizer1,0,wx.EXPAND | wx.ALL, 10)
        vbox.Add(wx.StaticLine(panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,10)
        vbox.Add(hbox1,0,wx.EXPAND | wx.ALL, 10)
        vbox.Add(hbox,0,wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(vbox)
        panel.Fit()

        if self.test_types.GetValue() == 'Turbo码内核测试':
            self.code_rate.Disable()

    def updateDisplay(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        self.DisplayText.AppendText(str(msg.data))

    def updateDisplay_gauge(self, msg): 
        t = msg.data
        self.m_gauge1.SetValue(t)
        self.m_staticText2.SetLabel("%s%%" % t)

    def OnChoose(self,event):
        if self.test_types.GetValue() == 'PDSCH测试':
            self.code_rate.Enable()
        if self.test_types.GetValue() == 'Turbo码内核测试':
            self.code_rate.Disable()

    def data_process(self):
        cmd_msg_list = []
        cmd_msg = ''
        if self.test_types.GetValue() == 'Turbo码内核测试':
            cmd_msg_list.append('-t turbo')
            cmd_msg_list.append('-r 0.3')
        elif self.test_types.GetValue() == 'PDSCH测试':
            cmd_msg_list.append('-t pdsch')
            cmd_msg_list.append('-r '+self.code_rate.GetValue())

        cmd_msg_list.append('-b '+self.block_txt.GetValue())
        cmd_msg_list.append('-d '+self.decode_txt.GetValue())
        cmd_msg_list.append('-i '+self.iterate_txt.GetValue())
        cmd_msg_list.append('-m '+self.modulation_txt.GetValue())
        cmd_msg_list.append('-n '+self.SNR_txt.GetValue())
        cmd_msg_list.append('--sova-delta '+self.sova_delta_txt.GetValue())

        if self.sova_fast.GetValue() ==True:
            cmd_msg_list.append('--sova-fast')
        if self.judge_txt.GetValue() =='硬判决':
            cmd_msg_list.append('--hard-demod')        

        for item in cmd_msg_list:
            cmd_msg = cmd_msg+item+' '
        return cmd_msg

    # 测试响应事件
    def OnTest(self,event):
        self.test_btn.Disable()
        self.DisplayText.Clear()
        self.m_gauge1.SetValue(0)
        ret_msg = self.data_process()
        # print ret_msg

        # self.p=subprocess.Popen('../../build/apps/c++/lte_test'+' '+ret_msg, 
        #     shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.p=subprocess.Popen('/usr/local/share/gr-lte_sat/examples/lte_test'+' '+ret_msg, 
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        thread1 = threading.Thread(target = self.start_server)
        thread1.start()   
        wx.MessageBox(u'\n测试可能需要很长时间\n\n请耐心等候...', caption=u'温馨提示', style=wx.OK)

    def start_server(self):
        global flag
        # self.stop_btn.Enable()
        i = 0
        while True:
            flag = 1            
            i = i+1
            buff = self.p.stdout.readline()
            if(i == 100):
                i = 0
            wx.CallAfter(Publisher().sendMessage, "update", buff)
            wx.CallAfter(Publisher().sendMessage, "update_gauge", i)
            if buff == '' and self.p.poll() != None:
                wx.CallAfter(Publisher().sendMessage, "update_gauge", 100)
                flag = 0
                self.test_btn.Enable()
                break  

        # # 结果写入文件
        # result_file = open("result.dat","w")
        # for entry in result:
        #     try:
        #         result_file.write(entry)
        #     except:
        #         pass
        # result_file.close()   

    def OnCloseWindow(self, event):
        global flag
        try:
            if flag == 1:
                dlg = wx.MessageDialog(self, u"\n测试正在进行...\n确认退出?", u"温馨提示", wx.YES_NO | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    self.Destroy()
                else:
                    pass
                dlg.Destroy()
            else:
             self.Destroy()                
        except:
            self.Destroy()

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = MainFrame(parent=None, id=-1)
    frame.Show()
    app.MainLoop()
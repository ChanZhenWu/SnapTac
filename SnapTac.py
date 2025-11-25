#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import re
import sys
import matplotlib
matplotlib.use('Agg')  # 设置为不显示图形的后端
matplotlib.use('pdf')  # 显式设置后端
import matplotlib.pyplot as plt
from PyPDF2 import PdfMerger
import math
import wx
import subprocess
from threading import Thread

class LogFileProcessor(wx.Frame):
		def __init__(self, parent, title):
				style = wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP		# 设置窗口的默认样式，显示在最顶端
				super(LogFileProcessor, self).__init__(parent, title=title, size=(800, 600))
				
				self.InitUI()
				self.Centre()
				self.Show()

				# 创建状态栏
				self.CreateStatusBar()
				self.SetStatusText("v0.95")
				
		def InitUI(self):
				panel = wx.Panel(self)
				vbox = wx.BoxSizer(wx.VERTICAL)

				# # 标题
				# title = wx.StaticText(panel, label=".log文件处理器")
				# title.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
				# vbox.Add(title, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

				# 创建菜单栏
				menubar = wx.MenuBar()
				
				# 创建 Help 菜单
				help_menu = wx.Menu()
				help_item = help_menu.Append(wx.ID_HELP, "Help Manual", "Open Help Documentation")
		
				# 绑定菜单事件
				self.Bind(wx.EVT_MENU, self.OnHelp, help_item)
		
				# 添加到菜单栏
				menubar.Append(help_menu, "Help")
				self.SetMenuBar(menubar)  # 设置菜单栏

				# 选择目录控件
				dir_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "")
				self.dir_picker = wx.DirPickerCtrl(
						panel, 
						message="Select log Path",
						style=wx.DIRP_USE_TEXTCTRL|wx.DIRP_DIR_MUST_EXIST
				)
				dir_box.Add(self.dir_picker, flag=wx.EXPAND|wx.ALL, border=5)
				vbox.Add(dir_box, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=10)

				# 输出格式选择+处理按钮区域
				hbox = wx.BoxSizer(wx.HORIZONTAL)		# 盒式布局管理器

				# 创建一个带标题 "feature:" 的静态框
				feature_box = wx.StaticBox(panel, label="feature visable")
				feature_sizer = wx.StaticBoxSizer(feature_box, wx.HORIZONTAL)
				
				# 3 个选项
				self.feature_choices = ['DeviceName', 'PadName', 'TPName']
				
				# 创建 3 个 CheckBox 并水平排列
				self.checkbox_device = wx.CheckBox(panel, label="DeviceName")
				self.checkbox_pad = wx.CheckBox(panel, label="PadName")
				self.checkbox_pin = wx.CheckBox(panel, label="TPName")
				
				# 默认选中第一个（可选）
				self.checkbox_device.SetValue(True)  # 默认勾选 DeviceName
				
				# 添加到 feature_sizer（水平排列）
				feature_sizer.Add(self.checkbox_device, flag=wx.ALL, border=5)
				feature_sizer.Add(self.checkbox_pad, flag=wx.ALL, border=5)
				feature_sizer.Add(self.checkbox_pin, flag=wx.ALL, border=5)
				
				# 添加到主水平布局 hbox
				hbox.Add(feature_sizer, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=20)
				
				# 处理按钮
				self.process_btn = wx.Button(panel, label="Run", size=(100, 50))
				self.process_btn.Bind(wx.EVT_BUTTON, self.OnProcess)
				hbox.Add(self.process_btn, flag=wx.ALIGN_CENTER_VERTICAL)
				
				# 将 hbox 添加到主垂直布局 vbox
				vbox.Add(hbox, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

				# 状态文本框
				status_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "")
				self.status_text = wx.TextCtrl(
						panel, 
						style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL,
						size=(-1, 200)
				)
				status_box.Add(self.status_text, proportion=1, flag=wx.EXPAND|wx.ALL, border=1)
				vbox.Add(status_box, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=1)
				panel.SetSizer(vbox)
				
				# 初始化状态
				self.UpdateStatus("* ScnapTac (v0.95)")
				self.UpdateStatus("* Author: Noon.Chen")
				self.UpdateStatus("-----" * 10)
				self.UpdateStatus("Ready, Please select board path to continue ...")
				self.UpdateStatus("-----" * 10)
		
		def UpdateStatus(self, message):
				"""更新状态文本框内容"""
				self.status_text.AppendText(message + "\n")	# 将指定的文本添加到控件现有内容的末尾，并自动换行
				# self.status_text.SetInsertionPointEnd()	# 将光标移动到文本的末尾
		
		def OnProcess(self, event):
				global DeviceName, PadName, TPName

				DeviceName = self.checkbox_device.GetValue()  # 直接获取当前选中的值
				self.UpdateStatus(f"DeviceName: {DeviceName}")

				PadName = self.checkbox_pad.GetValue()
				self.UpdateStatus(f"PadName: {PadName}")

				TPName = self.checkbox_pin.GetValue()
				self.UpdateStatus(f"TPName: {TPName}")

				selected_dir = self.dir_picker.GetPath()
				if not selected_dir:
						wx.MessageBox("Please select a path", "error", wx.OK | wx.ICON_ERROR)
						return
				
				# 禁用按钮防止重复点击
				self.process_btn.Disable()
				# self.UpdateStatus(f"Begin to handling: {selected_dir}")
				
				# 在后台线程中执行耗时操作
				worker = Thread(target=self.ProcessLogFiles, args=(selected_dir,))
				worker.start()

		def OnHelp(self, event):
				# 获取 PDF 路径（适配 PyInstaller 打包模式）
				if getattr(sys, 'frozen', False):
					# 打包后的路径
					base_path = sys._MEIPASS
				else:
					# 开发时的路径
					base_path = os.path.dirname(__file__)
	
				# 假设 help.pdf 放在程序目录下的 docs 文件夹
				pdf_path = os.path.join(os.path.dirname(__file__), "docs", "manual.pdf")
	
				if not os.path.exists(pdf_path):
						wx.MessageBox("Help file not found!", "Error", wx.OK | wx.ICON_ERROR)
						return
				
				# 跨平台打开 PDF
				try:
					if wx.Platform == "__WXMSW__":  # Windows
						os.startfile(pdf_path)
					elif wx.Platform == "__WXMAC__":  # macOS
						subprocess.Popen(["open", pdf_path])
					else:  # Linux
						subprocess.Popen(["xdg-open", pdf_path])
				except Exception as e:
					wx.MessageBox(f"Failed to open PDF: {e}", "Error", wx.OK | wx.ICON_ERROR)

		def ProcessLogFiles(self, directory):
        		# 确定前工作目录
				os.chdir(directory)
        		# print(f"OS.path: {os.getcwd()}")
				# self.UpdateStatus(f"OS.path: {os.getcwd()}")
				wx.CallAfter(self.UpdateStatus, f"OS.path: {os.getcwd()}")

				to_coverage = []
				tp_coverage = []
				borad_map = []
				# -----------------------------------------------------------------------------
				with open('testorder', 'r') as file:
					# print ('Parsing testorder ...')
					wx.CallAfter(self.UpdateStatus, 'Parsing testorder ...')
					for line in file:
						cover_dict = {}
						line = line.strip()
						line = re.sub(r'\s+', ' ', line)
						if '"' not in line:
							continue
						parts = line.split('"')  # 按双引号分割
						parts[1] = parts[1].upper()
						name = parts[1]
						parts[2] = parts[2][1:]
						parts[2] = parts[2].strip()
						if '%' in parts[1]:
							name = name[:name.find('%')]
						elif '_' in parts[1]:
							name = name[:name.find('_')]
						# print (name)
						cover_dict['name'] = name
						if parts[2] == '':
							cover_dict['status'] = 'true'
						elif 'nulltest' not in parts[2]:
							cover_dict['status'] = 'true'
						elif 'nulltest' in parts[2] and parts[2][9:] != '':
							cover_dict['status'] = 'may'
						elif parts[2] == 'nulltest':
							cover_dict['status'] = 'false'
						to_coverage.append(cover_dict)
				
				with open('testplan', 'r') as file:
					# print ('Parsing testplan ...')
					wx.CallAfter(self.UpdateStatus, 'Parsing testplan ...')
					for line in file:
						cover_dict = {}
						line = line.strip()
						line = re.sub(r'\s+', ' ', line)
						if '"' not in line:
							continue
						parts = line.split('"')  # 按双引号分割
						parts[0] = re.sub(r'\s+', '', parts[0])
						parts[1] = re.sub(r'\s+', '', parts[1])
						parts[1] = parts[1].upper()
						name = parts[1]
						if '/' in parts[1]:
							name = name[name.find('/')+1:]
							if '%' in name:
								name = name[:name.find('%')]
							elif '_' in name:
								name = name[:name.find('_')]
						elif '/' not in parts[1]:
							name = parts[1]
							if '%' in name:
								name = name[:name.find('%')]
							elif '_' in name:
								name = name[:name.find('_')]
						# print (name)
						if parts[0] == 'test':
							cover_dict['name'] = name
							cover_dict['status'] = 'true'
						elif 'test' in parts[0]:
							cover_dict['name'] = name
							cover_dict['status'] = 'false'
						if cover_dict != {}:
							tp_coverage.append(cover_dict)

				with open('board', 'r') as file:
					# print ('Parsing board ...')
					wx.CallAfter(self.UpdateStatus, 'Parsing board ...')
					for lines in file:
						node = []
						devpin = []
						lines = lines.strip()
						if lines == "CONNECTIONS":
							for lines in file:
								node_dict = {}
								lines = lines.strip()
								line = lines[:-1] if lines.endswith(';') else lines  # 检查后再切片
								# print (line)
								if '.' not in line:
									node = line
									# print (node)
								if '.' in line:
									devpin = line
									# print (devpin)
									node_dict['name'] = devpin
									node_dict['node'] = node
									borad_map.append(node_dict)
								if line == '':
									break

				# -----------------------------------------------------------------------------
				def calculate_y_axis_angle(point1, point2):
				    x1, y1 = point1
				    x2, y2 = point2
				
				    # 检查两点是否相同
				    if x1 == x2 and y1 == y2:
				        return 0.0  # 或返回 None，表示无法计算
				
				    delta_x = x2 - x1
				    delta_y = y2 - y1
				
				    # 计算相对于 X 轴的角度（弧度）
				    theta_rad = math.atan2(delta_y, delta_x)
				    theta_deg = math.degrees(theta_rad)
				
				    return theta_deg
				
				
				def rotate_box_y(box, degrees):
				    # 计算边界和中心点
				    min_x = min(p[0] for p in box)
				    max_x = max(p[0] for p in box)
				    min_y = min(p[1] for p in box)
				    max_y = max(p[1] for p in box)
				    
				    center_x = (min_x + max_x) / 2
				    center_y = (min_y + max_y) / 2
				    
				    # 转换为弧度
				    theta = math.radians(degrees)
				    cos_t = math.cos(theta)
				    sin_t = math.sin(theta)
				    
				    rotated_points = []
				    for x, y in box:
				        # 转换为相对中心点的坐标
				        rel_x = x - center_x
				        rel_y = y - center_y
				        
				        # 应用旋转（2D旋转）
				        new_x = rel_x * cos_t - rel_y * sin_t
				        new_y = rel_x * sin_t + rel_y * cos_t
				        
				        # 转换回绝对坐标并四舍五入到整数
				        new_x_abs = round(new_x + center_x)
				        new_y_abs = round(new_y + center_y)
				        
				        rotated_points.append((new_x_abs, new_y_abs))
				    
				    return rotated_points
    
				# -----------------------------------------------------------------------------
				
				frame_toutline = []
				frame_boutline = []
				frame_topdev = []
				frame_botdev = []
				coord_toppad = []
				coord_botpad = []
				toppin_map = []
				botpin_map = []
				toptp_map = []
				bottp_map = []
				tdev_map = []
				bdev_map = []
				# -----------------------------------------------------------------------------
				with open('board_xy', 'r') as file:
					# print ('Parsing board ...')
					wx.CallAfter(self.UpdateStatus, 'Parsing boardxy ...')
					for line in file:
						axis = []
						dev_dict = {}
						line = line.strip()
						if line == "OUTLINE":
							for line in file:
								line = line.strip()
								line = line[:-1] if line.endswith(';') else line  # 检查后再切片
								if line == '':
									break
								# print (line)
								axis.append(eval(line))
							frame_toutline = axis
							max_x = max(coord[0] for coord in axis)
							min_x = min(coord[0] for coord in axis)
							xlength = max_x + min_x
							# axis_image for bottom
							frame_boutline = [(xlength - x, y) for x, y in axis]
				
						if re.match('^NODE ', line):
							lines = line.split(' ')
							tpname = lines[1]
							for line in file:
								dev_dict = {}
								line = line.strip()
								line = re.sub(r'\s+', ' ', line)
								line = line[:-1] if line.endswith(';') else line  # 检查后再切片
								if line == 'ALTERNATES':
									continue
								if line == '' or line == 'EXTRAS':
									break
								lines = line.split(' ')
								lines[0] = lines[0][:-1]
								if lines[2] == 'TOP' and lines[3] == 'MANDATORY':
									axis = (int(lines[0]), int(lines[1]))
									item = next((d for d in toptp_map if d.get('name') == tpname), None)
									if item is None:
										dev_dict['name'] = tpname
										dev_dict['axis'] = [axis]
										toptp_map.append(dev_dict)
									else:
										axis_read = item['axis']
										axis_read.append(axis)
										dev_dict['axis'] = axis_read
								elif lines[2] == 'MANDATORY':
									axis = (xlength - int(lines[0]), int(lines[1]))
									item = next((d for d in bottp_map if d.get('name') == tpname), None)
									if item is None:
										dev_dict['name'] = tpname
										dev_dict['axis'] = [axis]
										bottp_map.append(dev_dict)
									else:
										axis_read = item['axis']
										axis_read.append(axis)
										dev_dict['axis'] = axis_read
				
						if line == "OTHER":
							for line in file:
								line = line.strip()
								line = re.sub(r'\s+', ' ', line)
								line = line[:-1] if line.endswith(';') else line  # 检查后再切片
								if line == '':
									break
								lines = line.split(' ')
								if len(lines) > 3:
									# print (lines[0],lines[1],lines[2],lines[3])
									dev_dict = {}
									tp_dict = {}
									devname = ''
									devpad = ''
									face = ''
									lines[0] = lines[0][:-1]
									if lines[3] == 'TOP':
										axis = (int(lines[0]), int(lines[1]))
										part = lines[2].split('.')
										devname = part[0]
										devpad = part[1]
										# print (axis, devname, devpad)
										coord_toppad.append(axis)
				
										# 判断零件是否已经存在列表中
										item = next((d for d in tdev_map if d.get('name') == devname), None)
										# print (item, devname, axis)
										if item is None:
											dev_dict['name'] = devname
											dev_dict['pad'] = [devpad]
											dev_dict['axis'] = [axis]
											tdev_map.append(dev_dict)
										else:
											axis_read = item['axis']
											axis_read.append(axis)
											# print (axis_read)
											dev_dict['axis'] = axis_read
											pad_read = item['pad']
											pad_read.append(devpad)
											# print (pad_read)
											dev_dict['pad'] = pad_read
										# 判断是否有TP
										if lines[4] == 'MANDATORY':
											item = next((d for d in borad_map if d.get('name') == lines[2]), None)
											if item is not None:
												# print (item['node'])
												devpad = item['node']
											tp_dict['name'] = devpad
											tp_dict['axis'] = [axis]
											toppin_map.append(tp_dict)
									else:
										# axis_image for bottom
										axis = (xlength - int(lines[0]), int(lines[1]))
										part = lines[2].split('.')
										devname = part[0]
										devpad = part[1]
										# print (axis, devname, devpad)
										coord_botpad.append(axis)
				
										# 判断零件是否已经存在列表中
										item = next((d for d in bdev_map if d.get('name') == devname), None)
										# print (item, devname, axis)
										if item is None:
											dev_dict['name'] = devname
											dev_dict['pad'] = [devpad]
											dev_dict['axis'] = [axis]
											bdev_map.append(dev_dict)
										else:
											axis_read = item['axis']
											axis_read.append(axis)
											# print (axis_read)
											dev_dict['axis'] = axis_read
											pad_read = item['pad']
											pad_read.append(devpad)
											# print (pad_read)
											dev_dict['pad'] = pad_read
										# 判断是否有TP
										if lines[3] == 'MANDATORY':
											item = next((d for d in borad_map if d.get('name') == lines[2]), None)
											if item is not None:
												# print (item['node'])
												devpad = item['node']
											tp_dict['name'] = devpad
											tp_dict['axis'] = [axis]
											botpin_map.append(tp_dict)
				
				# -----------------------------------------------------------------------------
					# 准备画图...
					for face in ('TOP', 'BOT'):
						if face == 'TOP':
							coords = coord_toppad
							coords_tp = toptp_map
							coords_pin = toppin_map
							outline = frame_toutline
							frame = tdev_map
						else:
							coords = coord_botpad
							coords_tp = bottp_map
							coords_pin = botpin_map
							outline = frame_boutline
							frame = bdev_map

						# 根据最外的4个角点+补偿值，形成新的*直角*外框
						max_olx = max(x for x, y in outline)
						min_olx = min(x for x, y in outline)
						max_oly = max(y for x, y in outline)
						min_oly = min(y for x, y in outline)
						olx = max_olx - min_olx
						oly = max_oly - min_oly
						orientation = 'horizontal' if olx > oly else 'vertical'

						# 创建图形
						# plt.figure(figsize = (20, 48))
						ratio = olx/oly
						if orientation == 'vertical':
							frameline = (float(50*ratio*1.2), 50)
						elif orientation == 'horizontal':
							frameline = (50, float(50/ratio*1.2))
						plt.figure(figsize = frameline)
				
						# 绘制 outline
						# print (f'plotting {face} Outline ...')
						wx.CallAfter(self.UpdateStatus, f'plotting {face} Outline ...')
						x_coords, y_coords = zip(*outline)
						plt.fill(x_coords, y_coords, color='skyblue', alpha=0.2, edgecolor='navy', linewidth=0.05)
						
						# 绘制 device frame
						# print (f'plotting {face} device frame & name ...')
						wx.CallAfter(self.UpdateStatus, f'plotting {face} device frame & name ...')
						for i, item in enumerate(frame, start=1):
							# print (item['name'])
							# print (item['axis'])
							to_status = ''
							tp_status = ''
							name = item['name']
							axis = item['axis']
							len_axis = len(item['axis'])
							
							to_item = next((d for d in to_coverage if d.get('name') == name), None)
							if to_item is not None:
								# print (to_item['status'])
								to_status = to_item['status']
							tp_item = next((d for d in tp_coverage if d.get('name') == name), None)
							if tp_item is not None:
								# print (tp_item['status'])
								tp_status = tp_item['status']
							if to_status == 'true' and tp_status == 'true':
								cls = 'green'
							elif to_status == 'true' and tp_status == 'false':
								cls = 'red'
							elif to_status == 'may' and tp_status == 'false':
								cls = 'red'
							elif to_status == 'may' and tp_item is None:
													cls = 'yellow'
							elif to_status == 'false' and tp_item is None:
													cls = 'red'
							elif to_status == 'false' and tp_status == 'false':
								cls = 'red'
							else:
								cls = 'silver'
								
							# 使用max/min函数和lambda表达式，找到最外的4个角点。
							x_max = max(axis, key=lambda x: x[0])
							x_min = min(axis, key=lambda x: x[0])
							y_max = max(axis, key=lambda x: x[1])
							y_min = min(axis, key=lambda x: x[1])
							# print (y_min, x_min, y_max, x_max)
							
							# 计算旋转角度
							if len_axis == 2:
								point1 = axis[0]
								point2 = axis[1]
							if len_axis > 2:
								point1 = y_min
								point2 = x_max
								point3 = y_min
								point4 = x_min
								angle1 = calculate_y_axis_angle(point3, point4)
								angle1 = angle1 - 90
								# print(f"两点相对于 Y 轴的旋转角度: {angle1}°")
							
							if len_axis >= 2:
								angle = calculate_y_axis_angle(point1, point2)
								# print(f"两点相对于 Y 轴的旋转角度: {angle}°")
								
								# 根据最外的4个角点+补偿值，形成新的*直角*外框
								max_x = max(x for x, y in axis)
								min_x = min(x for x, y in axis)
								max_y = max(y for x, y in axis)
								min_y = min(y for x, y in axis)
								Spin = False
								# print (max_x, min_x, max_y, min_y)
								if max_y == min_y and max_x != min_x:
									# print ('option a')
									max_y = max_y + 80
									min_y = min_y - 80
								elif max_y != min_y and max_x == min_x:
									# print ('option b')
									max_x = max_x + 80
									min_x = min_x - 80
								elif max_y != min_y and max_x != min_x and len_axis == 2 and (abs(angle) <= 1 or abs(angle) >= 179):
									# print ('option 1')
									max_y = max_y + 80
									min_y = min_y - 80
								elif max_y != min_y and max_x != min_x and len_axis == 2 and (abs(angle) >= 89 and abs(angle) <= 91):
									# print ('option 3')
									max_x = max_x + 80
									min_x = min_x - 80
								elif max_y != min_y and max_x != min_x and len_axis == 2 and ((abs(angle) > 1 and abs(angle) < 45) or (abs(angle) > 135 and abs(angle) < 179)):
									# print ('option 2')
									Spin = True
									max_y = max_y + 30
									min_y = min_y - 30
								elif max_y != min_y and max_x != min_x and len_axis == 2 and ((abs(angle) >= 45 and abs(angle) < 89) or (abs(angle) > 91 and abs(angle) <= 135)):
									# print ('option 2')
									Spin = True
									max_x = max_x + 50
									min_x = min_x - 50
								elif max_y != min_y and max_x != min_x and len_axis != 2:
									# print ('option c')
									Spin = True
									max_y = max_y + 80
									min_y = min_y - 80
									max_x = max_x + 80
									min_x = min_x - 80
	
								device_frame = [(max_x,min_y),(min_x,min_y),(min_x,max_y),(max_x,max_y)]
								gapx = max_x - min_x
								gapy = max_y - min_y
								spin_frame = [(max_x-gapx*0.1,min_y+gapy*0.1),(min_x+gapx*0.1,min_y+gapy*0.1),(min_x+gapx*0.1,max_y-gapy*0.1),(max_x-gapx*0.1,max_y-gapy*0.1)]
								
								# 旋转计算的度
								rotate_frame = rotate_box_y(device_frame, angle)
								frame_spin = rotate_box_y(spin_frame, angle)
								
								# print (x_coords, y_coords, Spin, abs(angle), cls)
								if len_axis == 2 and Spin:
									x_coords, y_coords = zip(*rotate_frame)
									plt.fill(x_coords, y_coords, color=cls, alpha=0.6, edgecolor='navy', linewidth=0.05)
									# print ('rotated1')
								elif len_axis == 2:
									x_coords, y_coords = zip(*device_frame)
									plt.fill(x_coords, y_coords, color=cls, alpha=0.6, edgecolor='navy', linewidth=0.05)
									# print ('not rotate1')
								elif len_axis > 2 and abs(angle - angle1) < 1:	# tolerace for < 1°
									x_coords, y_coords = zip(*frame_spin)
									plt.fill(x_coords, y_coords, color=cls, alpha=0.6, edgecolor='navy', linewidth=0.05)
									# print ('rotated2')
								elif len_axis > 2:
									x_coords, y_coords = zip(*device_frame)
									plt.fill(x_coords, y_coords, color=cls, alpha=0.6, edgecolor='navy', linewidth=0.05)
									# print ('not rotate2')
	
								visable = 0.8 if DeviceName else 0
				 				# 计算图形中心位置
								center_x = (max_x + min_x)/2
								center_y = (max_y + min_y)/2
								rotate = 90 if max_y - min_y > max_x - min_x else 0
				      	
								# 字体大小
								length = max_y - min_y if max_y - min_y > max_x - min_x else max_x - min_x
								fsize = next((v for l, v in [(5000, 12), (3000, 8), (1500, 4), (800, 2)] if length > l), 1)
				      	
								# 在图形正中间添加名称
								plt.text(center_x, center_y, name, ha='center', va='center', alpha=visable, fontsize=fsize, color='black', rotation=rotate,
				 									 bbox=dict(facecolor='none', edgecolor='none', alpha=0.1, boxstyle='round'))
							
								visable = 0.6 if PadName else 0
								# 写入 pad 名称
								x_coords, y_coords = zip(*axis)
								x_max = max(x_coords)
								x_min = min(x_coords)
								y_max = max(y_coords)
								y_min = min(y_coords)
								padname = item['pad']
								for x_coord, y_coord, name in zip(x_coords, y_coords, padname):
									# print (name, x_coord, y_coord)
									# if x_coord == x_max or x_coord == x_min or y_coord == y_max or y_coord == y_min:
									plt.text(x_coord, y_coord, name, ha='center', va='center', alpha=visable, fontsize=1, color='orange', rotation=0)

						# 绘制 pad
						# print (f'plotting {face} Pad ...')
						wx.CallAfter(self.UpdateStatus, f'plotting {face} Pad ...')
						x_coords, y_coords = zip(*coords)
						plt.scatter(x_coords, y_coords, c='green', marker='h', s=3.0, alpha=0.8, edgecolors='black', linewidths=0.02)
				
						# 绘制 probed pin
						# print (f'plotting {face} probed pin ...')
						wx.CallAfter(self.UpdateStatus, f'plotting {face} probed pin ...')
						for i, item in enumerate(coords_pin, start=1):
							tpname = item['name']
							axis = item['axis']
							# print (name, axis)
							x_coords, y_coords = zip(*axis)
							plt.scatter(x_coords, y_coords, c='red', marker='o', s=4.0, alpha=0.8, edgecolors='black', linewidths=0.02)
							visable = 0.4 if TPName else 0
							# 写入TP name
							for x_coord, y_coord in zip(x_coords, y_coords):
								plt.text(x_coord, y_coord, tpname, ha='center', va='center', alpha=visable, fontsize=1, color='black', rotation=0)
				
						# 绘制 TP
						# print (f'plotting {face} TP ...')
						wx.CallAfter(self.UpdateStatus, f'plotting {face} TP ...')
						for i, item in enumerate(coords_tp, start=1):
							tpname = item['name']
							axis = item['axis']
							# print (name, axis)
							x_coords, y_coords = zip(*axis)
							plt.scatter(x_coords, y_coords, c='red', marker='o', s=4.0, alpha=0.8, edgecolors='black', linewidths=0.02)
							visable = 0.4 if TPName else 0
							# 写入TP name
							for x_coord, y_coord in zip(x_coords, y_coords):
								plt.text(x_coord, y_coord, tpname, ha='center', va='center', alpha=visable, fontsize=1, color='black', rotation=0)
						
						# 设置图形属性
						plt.title(f'board layer-({face})', fontsize=48)
						plt.tick_params(axis='both', which='both', direction='in', length=4, width=0.5, grid_alpha=0.5, pad=2, labelsize=12, )
						plt.xlabel('X axis, scale: 0.1 mils', fontsize=32)
						plt.ylabel('Y axis, scale: 0.1 mils', fontsize=32)
						plt.locator_params(axis='both', nbins=20)  # 两轴分成 20 个刻度密度
						plt.grid(True, axis='both', linestyle='--', color='gray', alpha=0.3, which='major', linewidth=0.05)
						plt.axis('equal')  # 保持纵横比一致
						# 保存图形
						# print (f'saving {face} data ...')
						wx.CallAfter(self.UpdateStatus, f'saving {face} data ...')
						plt.savefig(f'board layer-({face}).pdf', format='pdf', dpi=300, bbox_inches='tight')
						# 显示图形
						# plt.show()
				
					merger = PdfMerger()
					# 添加要合并的PDF文件
					merger.append('board layer-(TOP).pdf')
					merger.append('board layer-(BOT).pdf')
						# 写入输出文件
					# print ("merging into 'board layer.pdf' ...")
					wx.CallAfter(self.UpdateStatus, "merging into 'board layer.pdf' ...")
					merger.write('board layer.pdf')
					merger.close()
					os.remove('board layer-(TOP).pdf')
					os.remove('board layer-(BOT).pdf')
					# self.UpdateStatus("\n\t<completed>")
					wx.CallAfter(self.UpdateStatus, "\t<completed>")
					sys.exit()

if __name__ == '__main__':
		app = wx.App()
		LogFileProcessor(None, title="SnapTac")
		app.MainLoop()










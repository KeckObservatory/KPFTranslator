# List of GUIs for KPF
GUI_list = [
            # Control0 for DSI
            # Control1
            # - add Spectrograph GUI
            {'name': 'KPF Fiber Injection Unit (FIU)',
             'cmd': ['kpf', 'start', 'fiu_gui'],
             'display': 'control1',
             'position': '0,80,50,-1,-1'},
            {'name': 'KPF Exposure Meter',
             'cmd': ['kpf', 'start', 'emgui'],
             'display': 'control1',
             'position': '0,5,550,-1,-1'},
            # Control2
            # - add Eventsounds
            {'name': 'SAOImage kpfds9',
             'cmd':  ['kpf', 'start', 'kpfds9'],
             'display': 'control2',
             'position': '0,1,55,1800,900'},
            # Telstatus
            # - add Tip Tilt GUI
            {'name': 'xshow_TipTilt',
             'cmd':  ['/home/kpfeng/bin/xshow_tiptilt'],
             'display': 'telstatus',
             'position': '0,1020,5,200,310'},
            {'name': 'KECK 1 FACSUM',
             'cmd':  ['xterm', '-T', 'xterm KECK 1 FACSUM', '-e', 'ssh', '-X', 'k1ruts@vm-k1obs', 'Facsum', '-k1'],
             'display': 'telstatus',
             'position': '0,250,10,-1,-1'},
            {'name': 'KECK 1 MET',
             'cmd':  ['xterm', '-T', 'xterm KECK 1 MET', '-e', 'ssh', '-X', 'k1ruts@vm-k1obs', 'Met', '-k1'],
             'display': 'telstatus',
             'position': '0,250,535,-1,-1'},
            {'name': 'MAGIQ - Observer UI',
             'cmd':  ['xterm', '-T', 'xterm MAGIQ - Observer UI', '-e', 'ssh', '-X', 'k1ruts@k1-magiq-server', 'magiq', 'start', 'ObserverUI'],
             'display': 'telstatus',
             'position': '0,500,15,-1,-1'},
            ]

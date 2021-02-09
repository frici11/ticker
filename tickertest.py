import PySimpleGUI as sg
import random
import time
from ticker import *
from threading import Thread


def datafeed():
    global feedlock
    nount = (" FOX", " DOG")
    prev = ("","")
    while running:
        if not feedlock:
            tcolor = random.choice((("white","black"), ("black","white"),
                     ("yellow","black"), ("red","white"), ("blue","gray60")))
            if tcolor != prev:
                prev = tcolor
                adjt = random.choice((("QUICK BROWN", "LAZY"), ("BROWN QUICK", "LAZY"),
                                      ("LAZY BROWN", "QUICK"), ("BROWN LAZY", "QUICK")))
                adj = random.randint(0,1)
                noun = random.randint(0,1)
                s1 = "THE " + adjt[adj] + nount[noun] + " JUMPS OVER THE " \
                           + adjt[1 - adj] + nount[1 - noun]
                tcj.push(s1, tcolor, "bold")

            curr = random.choices(("AUD","CAD","CHF","DKK","EUR","GBP",
                                   "HKD","JPY","NOK","NZD","SEK","USD"), k=2)
            if curr[0] != curr[1]:
                course_mark = random.randint(0,2)
                tcolor = ("red2","blue2","dark green")[course_mark]
                s2 = curr[0] + curr[1] + "▼=▲"[course_mark] \
                  + "{:.2f}".format(random.randint(50, 250) / 100)
                tcs.push(s2, tcolor)
        time.sleep(0.1)


sg.theme("SandyBeach")
PANELW, PANELH = 600, 26
t1mode = 1


colleft = [
    [sg.Text("TICKERS MODE")],
    [sg.Text("upper:", pad=((20, 0), (0, 0))),
     sg.Radio("tape", "mode", key="_MODES_", enable_events=True, default=True),
     sg.Radio("fade", "mode", key="_MODEF_", enable_events=True)],
    [sg.Text("lower:", pad=((20, 0), (0, 0))),
     sg.Radio("tape", "dummy", default=True)]
]
colright = [
    [sg.Text("CONTROL")],
    [sg.Text("tape speed (1-5) :", pad=((20, 0), (0, 0))),
     sg.Spin(values=[i for i in range(1,6)], initial_value=3, readonly=True,
             size=(2,1), enable_events=True, key="_SPEED_")],
     [sg.Text("data feed:", pad=((20, 0), (0, 0))),
      sg.Checkbox("paused", key="_FEED_", enable_events=True)],
]
layout = [
    [sg.Text("\nTEST SCREEN FOR NEWS TICKER",
             font="Any 26 bold", size=(28,3), justification="center")],
    [sg.Text("This is the working area, here can be placed anything and can be "
             "used independently from the tickers (grey stripes at the bottom).",
             font="Any 20", size=(37,5), justification="center")],
    [sg.HorizontalSeparator(pad=((0,0),(0,5)))],
    [sg.Column(colleft), sg.VerticalSeparator(),
     sg.Column(colright), sg.VerticalSeparator(),
     sg.Button("Start", size=(12,2), pad=((50,0),(0,0)), key="_STST_")],
    [sg.HorizontalSeparator(pad=((0,0),(10,15)))],
    [TickerJoint((PANELW,PANELH), (0,0), (PANELW,PANELH),
              pad=((0,0),(0,0)), key="_TJ_")],
    [TickerSplit((PANELW,PANELH), (0,0), (PANELW,PANELH),
              pad=((0,0),(0,10)), key="_TS_")]
]

window = sg.Window("NEWS TICKER", layout, finalize=True)
tcj = window["_TJ_"]
tcj.load(PANELW, PANELH, t1mode, 20, 15, "white", "gray40", (2, 1, 0.5))
tcs = window["_TS_"]
tcs.load(PANELW, PANELH, 20, 15, 15, "gray70")

running = feedlock = False
leap = 0
timeout_ms = 5

random.seed()

while True:
    event, values = window.read(timeout_ms)
    if event == sg.WIN_CLOSED:
        break
    if event in ("_MODES_", "_MODEF_"):
        t1mode = 1 if (event == "_MODES_") else 2
        tcj.reset(t1mode)
    elif event == "_STST_":
        if running:
            window[event].Update("Start")
            running = False
        else:
            window[event].Update("Stop")
            running = True
            feedlock = False
            window["_FEED_"].Update(0)
            leap = 0
            Thread(target=datafeed, daemon=True).start()
    elif event == "_FEED_":
        feedlock = values[event]
        if feedlock:
            tcj.clear()
            tcs.clear()
    elif event == "_SPEED_":
        timeout_ms = (6 - values[event]) * 2 - 1
    elif event == "__TIMEOUT__":
        if running:
            leap += 1
            if leap % 2 == 0:
                tcj.run()
            if leap % 3 == 0:
                tcs.run()

window.close()

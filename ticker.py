import PySimpleGUI as sg
import time


def _figure_x1(g, figure_id):
    return g.get_bounding_box(figure_id)[0][0]

def _figure_x2(g, figure_id):
    return g.get_bounding_box(figure_id)[1][0]


class TickerJoint(sg.Graph):

    def load(self, width, height, mode, fig_y, xmargin, tcolor, bcolor, fade_time):
        """
        Initial settings
        width  : width of Graph
        height : height of Graph
        mode   : 1 = pulling tape ; 2 = fading
        fig_y  : y coordinate of text figures
        xmargin: margin width on left and right side
        tcolor : text color in mode 1
        bcolor : background color in mode 1
        """
        self.textcolor = tcolor
        self.width = width
        self.height = height
        self.fig_y = fig_y
        self.xmargin = xmargin
        self.bgrcolor = bcolor
        self.space = " +++ "
        self.maxpending = 2
        self.tloc = sg.TEXT_LOCATION_TOP_LEFT
        self.fade_loop = 40
        self.fade_time = (fade_time[0] * 1000000000,
                          fade_time[1] * 1000000000 / self.fade_loop,
                          fade_time[2] * 1000000000)
        self._init(mode)
        self.rectleft = self.draw_rectangle((0, 0), (self.xmargin, self.height),
                            fill_color=self.bgrcolor, line_width=0)
        self.rectright = self.draw_rectangle((self.width - self.xmargin, 0), (self.width, self.height),
                            fill_color=self.bgrcolor, line_width=0)

    def reset(self, mode):
        self.delete_figure(self.text_fig)
        self.delete_figure(self.left_fig)
        self.TKCanvas.itemconfig(self.rectleft, fill=self.bgrcolor)
        self.TKCanvas.itemconfig(self.rectright, fill=self.bgrcolor)
        self._init(mode)

    def _init(self, mode):
        self.mode = mode
        self.state = 0
        self.last_ns = 0
        self.queue = []
        self.text = ""
        self.last_bgrcolor = ""
        self.Update(background_color=self.bgrcolor)
        if mode == 1:
            self.left_fig = self.draw_text("", (self.xmargin, self.fig_y),
                                    font="Any 10", color=self.bgrcolor, text_location=self.tloc)
            self.text_fig = self.draw_text("", (self.xmargin, self.fig_y),
                                    font="Any 10", color=self.textcolor, text_location=self.tloc)

    def run(self):
        self._tape() if self.mode == 1 else self._fade()

    def _tape(self):
        self.move_figure(self.text_fig, -1, 0)
        self.move_figure(self.left_fig, -1, 0)
        if _figure_x2(self, self.left_fig) < self.xmargin + 1:  # leftmost character disappeared
            self.text = self.text[1:]  # cut off the leftmost character
            if _figure_x2(self, self.text_fig) < self.width + 50:  # text running out
                # check for new data
                if len(self.queue) > 0:
                    while _figure_x2(self, self.text_fig) < self.width + 1:
                        # fill up the text until the end
                        # because new data must be scrolled from the right edge
                        self.delete_figure(self.text_fig)
                        self.text += " "
                        self.text_fig = self.draw_text(self.text, (self.xmargin, self.fig_y),
                                        font="Any 10", color=self.textcolor, text_location=self.tloc)
                    self.text += self.queue[0]["out"] + self.space
                    self.queue.pop(0)
            self.delete_figure(self.text_fig)
            self.delete_figure(self.left_fig)
            # indicator character has to be drawn at first, for not covering the text
            self.left_fig = self.draw_text(self.text[:1], (self.xmargin, self.fig_y),
                                    font="Any 10", color=self.bgrcolor, text_location=self.tloc)
            self.text_fig = self.draw_text(self.text, (self.xmargin, self.fig_y),
                                    font="Any 10", color=self.textcolor, text_location=self.tloc)
            self.bring_figure_to_front(self.rectleft)
            self.bring_figure_to_front(self.rectright)
        return

    def _fade(self):

        def rgb_get(n):
            return n >> 8

        def rgb_set(n1, n2, scale):
            return round(n1 + (n2 - n1) * scale)

        if self.state == 0:
            if len(self.queue) > 0:
                tcolor, bcolor = self.queue[0]["color"]
                self.text_fig = self.draw_text(self.queue[0]["out"], (self.width / 2, self.height / 2),
                                color=tcolor, font=self.queue[0]["font"],
                                text_location=sg.TEXT_LOCATION_CENTER)
                if bcolor not in ("", self.last_bgrcolor):
                    self.Update(background_color=bcolor)
                    self.TKCanvas.itemconfig(self.rectleft, fill=bcolor)
                    self.TKCanvas.itemconfig(self.rectright, fill=bcolor)
                    self.last_bgrcolor = bcolor
                self.queue.pop(0)
                rgb_tuple = self.TKCanvas.winfo_rgb(self.TKCanvas.itemcget(self.text_fig, "fill"))
                self.rgb1 = tuple(map(rgb_get, rgb_tuple))
                rgb_tuple = self.TKCanvas.winfo_rgb(self.TKCanvas["bg"])
                self.rgb2 = tuple(map(rgb_get, rgb_tuple))
                self.state = 1
                self.last_ns = time.monotonic_ns()
        elif self.state == 1:
            if time.monotonic_ns() - self.last_ns >= self.fade_time[0] and len(self.queue) > 0:
                self.last_ns = time.monotonic_ns()
                self.state = 2
                self.fade_counter = 1
        elif self.state == 2:
            if self.fade_counter > self.fade_loop:
                self.delete_figure(self.text_fig)
                self.last_ns = time.monotonic_ns()
                self.state = 3
            elif time.monotonic_ns() - self.last_ns >= self.fade_time[1]:
                scale = self.fade_counter / self.fade_loop
                rgb = tuple(map(rgb_set, self.rgb1, self.rgb2, ((scale,) * 3)))
                self.TKCanvas.itemconfig(self.text_fig, fill="#%02x%02x%02x" % rgb)
                self.fade_counter += 1
                self.last_ns = time.monotonic_ns()
        elif self.state == 3:
            if time.monotonic_ns() - self.last_ns >= self.fade_time[2]:
                self.state = 0
        return

    def push(self, text, color, emphasis=""):
        if len(self.queue) < self.maxpending:
            font = ("Any 10 " + emphasis).rstrip()
            self.queue.append({"out": text, "color": color, "font": font})
            return True
        return False

    def clear(self):
        self.queue.clear()
        return


class TickerSplit(sg.Graph):

    def load(self, width, height, fig_y, xmargin, safe_dist, bcolor):
        """
        Initial settings
        width    : width of Graph
        height   : height of Graph
        fig_y    : y coordinate of text figures
        xmargin  : margin width on left and right side
        safe_dist: distance betwwen two items
        bcolor   : background color
        """
        self.left_fig = -1
        self.fig_y = 20
        self.width = width
        self.height = height
        self.fig_y = fig_y
        self.xmargin = xmargin
        self.safe_dist = safe_dist
        self.bgrcolor = bcolor
        self.refine = False
        self.maxpending = 2
        self.tloc = sg.TEXT_LOCATION_TOP_LEFT
        self.Update(background_color=bcolor)
        self.rectleft = self.draw_rectangle((0, 0), (self.xmargin, self.height),
                                fill_color=bcolor, line_width=0)
        self.rectright = self.draw_rectangle((self.width - self.xmargin, 0), (self.width, self.height),
                                fill_color=bcolor, line_width=0)
        self._init()

    def reset(self):
        for t2 in self.text:
            self.delete_figure(t2["fig"])
        self.delete_figure(self.left_fig)
        self.text_fig = 0
        self.left_fig = 0
        self._init()

    def _init(self):
        self.queue = []
        self.text = []

    def run(self):

        def data_gate():
            ok = True
            if len(self.queue) == 0:
                ok = False
            elif len(self.text) > 0:
                ok = (_figure_x1(self, self.text[-1]["fig"]) + 1 <= self.width - self.xmargin)
                # last item has just appeared
            return ok

        def refine(tx_old, tx_new):
            # correction of items location, just for safety...
            # needless if all computations are accurate
            if tx_new != tx_old:
                for t2 in self.text[1:]:
                    self.move_figure(t2["fig"], tx_new - tx_old, 0)
        
        is_text = (len(self.text) > 0)
        if data_gate():
            newtext = self.queue[0]["out"]
            tcolor = self.queue[0]["color"]
            font = self.queue[0]["font"]
            if is_text:
                tx = max(self.width, _figure_x2(self, self.text[-1]["fig"]) + self.safe_dist)
            else:
                tx = self.width
            lfig = self.draw_text(newtext[:1], (tx, self.fig_y),
                        font=font, color=self.bgrcolor, text_location=self.tloc)
            tfig = self.draw_text(newtext, (tx, self.fig_y),
                        font=font, color=tcolor, text_location=self.tloc)
            self.text.append({"out": newtext, "fig": tfig, "color": tcolor, "font": font})
            self.queue.pop(0)
            if not is_text:
                self.left_fig = lfig
        if is_text:
            for t2 in self.text:
                self.move_figure(t2["fig"], -1, 0)
            self.move_figure(self.left_fig, -1, 0)
            if _figure_x2(self, self.left_fig) <= self.xmargin + 1: # leftmost character disappeared
                if len(self.text[0]["out"]) > 1:                    # the item still has content
                    self.text[0]["out"] = self.text[0]["out"][1:]   # cut off the leftmost character
                    tx = _figure_x2(self, self.text[0]["fig"])
                    self.delete_figure(self.text[0]["fig"])
                    self.delete_figure(self.left_fig)
                    self.left_fig = self.draw_text(self.text[0]["out"][:1], (self.xmargin, self.fig_y),
                                    font=self.text[0]["font"], color=self.bgrcolor, text_location=self.tloc)
                    tfig = self.draw_text(self.text[0]["out"], (self.xmargin, self.fig_y),
                                    font=self.text[0]["font"], color=self.text[0]["color"], text_location=self.tloc)
                    self.text[0]["fig"] = tfig
                    if self.refine:
                        refine(tx, _figure_x2(self, tfig))
                else:                                               # out of content
                    self.delete_figure(self.text[0]["fig"])
                    self.delete_figure(self.left_fig)
                    self.text.pop(0)
                    if len(self.text) > 0:
                        tx = _figure_x1(self, self.text[0]["fig"])
                        self.left_fig = self.draw_text(self.text[0]["out"][:1], (tx + 1, self.fig_y),
                                        font=self.text[0]["font"], color=self.bgrcolor, text_location=self.tloc)
                        self.send_figure_to_back(self.left_fig)
                    else:
                        self.left_fig = -1

            self.bring_figure_to_front(self.rectleft)
            self.bring_figure_to_front(self.rectright)
        return

    def push(self, text, color, emphasis=""):
        if len(self.queue) < self.maxpending:
            font = ("Any 10 " + emphasis).rstrip()
            self.queue.append({"out": text, "color": color, "font": font})
            return True
        return False

    def clear(self):
        self.queue.clear()
        return

if __name__ == "__main__":
    s0 = {f for f in dir(sg.Graph) if not f.startswith("_")}
    s1 = {f for f in dir(TickerJoint) if not f.startswith("_")}
    print("TickerJoint:", " ".join(s1.difference(s0)))
    print(TickerJoint.load.__doc__)
    s1 = {f for f in dir(TickerSplit) if not f.startswith("_")}
    print("TickerSplit:", " ".join(s1.difference(s0)))
    print(TickerSplit.load.__doc__)
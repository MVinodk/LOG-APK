
# Full Kivy app replicating Tkinter layout: IN / OUT tabs, summary with date range and bar/pie charts,
# Excel persistence with original columns, and update option.
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.core.window import Window
from datetime import datetime
import pandas as pd, os
from update_checker import UpdateChecker
import matplotlib.pyplot as plt

# Keep window size reasonable for testing on desktop; ignored on Android
Window.size = (800, 600)

DATAFILE = "industry_log.xlsx"
COLUMNS = ["Date","Time","Direction","Vehicle","Driver","Item","Type","Quantity","Rate",
           "Total","GST%","CGST","SGST","IGST","GrandTotal","Supplier","Notes"]

def ensure_datafile():
    if os.path.exists(DATAFILE):
        try:
            df = pd.read_excel(DATAFILE)
            missing = [c for c in COLUMNS if c not in df.columns]
            if missing:
                new = pd.DataFrame(columns=COLUMNS)
                for c in df.columns:
                    if c in new.columns:
                        new[c] = df[c]
                new.to_excel(DATAFILE, index=False)
        except Exception:
            df = pd.DataFrame(columns=COLUMNS)
            df.to_excel(DATAFILE, index=False)
    else:
        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(DATAFILE, index=False)

ensure_datafile()

class EntryForm(GridLayout):
    def __init__(self, direction="IN", **kwargs):
        super().__init__(**kwargs)
        self.cols = 2
        self.direction = direction
        self.padding = 10
        self.spacing = 6
        # Create fields similar to original logic
        self.date = TextInput(text=datetime.now().strftime("%Y-%m-%d"), multiline=False)
        self.time = TextInput(text=datetime.now().strftime("%H:%M:%S"), multiline=False)
        self.vehicle = TextInput(multiline=False)
        self.driver = TextInput(multiline=False)
        self.item = TextInput(multiline=False)
        self.type_ = TextInput(multiline=False)
        self.quantity = TextInput(text="0", multiline=False)
        self.rate = TextInput(text="0", multiline=False)
        self.gst = TextInput(text="18", multiline=False)
        self.supplier = TextInput(multiline=False)
        self.notes = TextInput(multiline=False)
        # Add widgets
        self.add_widget(Label(text="Date"))
        self.add_widget(self.date)
        self.add_widget(Label(text="Time"))
        self.add_widget(self.time)
        self.add_widget(Label(text="Vehicle"))
        self.add_widget(self.vehicle)
        self.add_widget(Label(text="Driver"))
        self.add_widget(self.driver)
        self.add_widget(Label(text="Item"))
        self.add_widget(self.item)
        self.add_widget(Label(text="Type"))
        self.add_widget(self.type_)
        self.add_widget(Label(text="Quantity"))
        self.add_widget(self.quantity)
        self.add_widget(Label(text="Rate"))
        self.add_widget(self.rate)
        self.add_widget(Label(text="GST%"))
        self.add_widget(self.gst)
        self.add_widget(Label(text="Supplier"))
        self.add_widget(self.supplier)
        self.add_widget(Label(text="Notes"))
        self.add_widget(self.notes)

    def get_row(self):
        try:
            q = float(self.quantity.text or 0)
        except Exception:
            q = 0.0
        try:
            r = float(self.rate.text or 0)
        except Exception:
            r = 0.0
        total = q * r
        try:
            gst_pct = float(self.gst.text or 0)
        except Exception:
            gst_pct = 0.0
        cgst = sgst = total * (gst_pct/2)/100
        igst = 0.0
        grand = total + cgst + sgst + igst
        row = {
            "Date": self.date.text,
            "Time": self.time.text,
            "Direction": self.direction,
            "Vehicle": self.vehicle.text,
            "Driver": self.driver.text,
            "Item": self.item.text,
            "Type": self.type_.text,
            "Quantity": q,
            "Rate": r,
            "Total": total,
            "GST%": gst_pct,
            "CGST": round(cgst,2),
            "SGST": round(sgst,2),
            "IGST": round(igst,2),
            "GrandTotal": round(grand,2),
            "Supplier": self.supplier.text,
            "Notes": self.notes.text
        }
        return row

class SummaryPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        top = GridLayout(cols=4, size_hint_y=None, height=40, padding=6, spacing=6)
        self.start_input = TextInput(text=(datetime.now().strftime("%Y-%m-01")), multiline=False)
        self.end_input = TextInput(text=(datetime.now().strftime("%Y-%m-%d")), multiline=False)
        top.add_widget(Label(text="Start Date (YYYY-MM-DD)"))
        top.add_widget(self.start_input)
        top.add_widget(Label(text="End Date (YYYY-MM-DD)"))
        top.add_widget(self.end_input)
        self.add_widget(top)
        btns = BoxLayout(size_hint_y=None, height=40, padding=6, spacing=6)
        gen_btn = Button(text="Generate Summary")
        gen_btn.bind(on_release=self.generate_summary)
        export_btn = Button(text="Export CSV")
        export_btn.bind(on_release=self.export_csv)
        btns.add_widget(gen_btn)
        btns.add_widget(export_btn)
        self.add_widget(btns)
        # area for images
        imgs = BoxLayout(orientation="horizontal")
        self.bar_img = Image()
        self.pie_img = Image()
        imgs.add_widget(self.bar_img)
        imgs.add_widget(self.pie_img)
        self.add_widget(imgs)

    def generate_summary(self, *args):
        s = self.start_input.text.strip()
        e = self.end_input.text.strip()
        try:
            df = pd.read_excel(DATAFILE)
        except Exception:
            popup = Popup(title="Error", content=Label(text="No data file found."), size_hint=(0.6,0.3))
            popup.open()
            return
        try:
            df['Date'] = pd.to_datetime(df['Date'])
            start = pd.to_datetime(s)
            end = pd.to_datetime(e)
        except Exception:
            popup = Popup(title="Error", content=Label(text="Invalid date format. Use YYYY-MM-DD"), size_hint=(0.6,0.3))
            popup.open()
            return
        mask = (df['Date']>=start) & (df['Date']<=end)
        sub = df.loc[mask]
        if sub.empty:
            popup = Popup(title="No Data", content=Label(text="No entries in selected range."), size_hint=(0.6,0.3))
            popup.open()
            return
        # bar: totals by Date
        agg = sub.groupby(sub['Date'].dt.date)['GrandTotal'].sum()
        fig1, ax1 = plt.subplots(figsize=(6,4))
        agg.plot(kind='bar', ax=ax1)
        ax1.set_title("Total by Date")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Total")
        barfile = "bar_summary.png"
        fig1.tight_layout()
        fig1.savefig(barfile)
        plt.close(fig1)
        # pie: distribution by Item (top 8)
        pieagg = sub.groupby('Item')['GrandTotal'].sum().sort_values(ascending=False).head(8)
        fig2, ax2 = plt.subplots(figsize=(6,4))
        ax2.pie(pieagg.values, labels=pieagg.index, autopct='%1.1f%%')
        ax2.set_title("Top items by value")
        piefile = "pie_summary.png"
        fig2.tight_layout()
        fig2.savefig(piefile)
        plt.close(fig2)
        # update images in UI
        self.bar_img.source = barfile
        self.bar_img.reload()
        self.pie_img.source = piefile
        self.pie_img.reload()

    def export_csv(self, *args):
        try:
            df = pd.read_excel(DATAFILE)
            out = "industry_log_export.csv"
            df.to_csv(out, index=False)
            popup = Popup(title="Exported", content=Label(text=f"CSV exported to {out}"), size_hint=(0.6,0.3))
            popup.open()
        except Exception:
            popup = Popup(title="Error", content=Label(text="Failed to export CSV"), size_hint=(0.6,0.3))
            popup.open()

class MainApp(TabbedPanel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_default_tab = False

        # IN tab
        tab_in = TabbedPanelItem(text="IN")
        in_layout = BoxLayout(orientation="vertical")
        self.in_form = EntryForm(direction="IN", size_hint_y=None)
        in_layout.add_widget(self.in_form)
        save_in = Button(text="Save IN Entry", size_hint_y=None, height=44)
        save_in.bind(on_release=self.save_in)
        in_layout.add_widget(save_in)
        tab_in.add_widget(in_layout)
        self.add_widget(tab_in)

        # OUT tab
        tab_out = TabbedPanelItem(text="OUT")
        out_layout = BoxLayout(orientation="vertical")
        self.out_form = EntryForm(direction="OUT", size_hint_y=None)
        out_layout.add_widget(self.out_form)
        save_out = Button(text="Save OUT Entry", size_hint_y=None, height=44)
        save_out.bind(on_release=self.save_out)
        out_layout.add_widget(save_out)
        tab_out.add_widget(out_layout)
        self.add_widget(tab_out)

        # Summary tab
        tab_sum = TabbedPanelItem(text="Summary")
        tab_sum.add_widget(SummaryPanel())
        self.add_widget(tab_sum)

        # Update tab
        tab_upd = TabbedPanelItem(text="Update")
        upd_layout = BoxLayout(orientation="vertical", padding=6, spacing=6)
        chk_btn = Button(text="Check for Updates", size_hint_y=None, height=44)
        chk_btn.bind(on_release=self.check_updates)
        upd_layout.add_widget(chk_btn)
        self.upd_status = Label(text="Current version: 1.0.0")
        upd_layout.add_widget(self.upd_status)
        tab_upd.add_widget(upd_layout)
        self.add_widget(tab_upd)

    def save_in(self, *args):
        row = self.in_form.get_row()
        self._append_row(row)
    def save_out(self, *args):
        row = self.out_form.get_row()
        self._append_row(row)
    def _append_row(self, row):
        try:
            df = pd.read_excel(DATAFILE)
        except Exception:
            df = pd.DataFrame(columns=COLUMNS)
        # ensure all columns
        for c in COLUMNS:
            if c not in df.columns:
                df[c] = None
        df = df.append(row, ignore_index=True)
        df.to_excel(DATAFILE, index=False)
        Popup(title="Saved", content=Label(text="Entry saved"), size_hint=(0.6,0.3)).open()

    def check_updates(self, *args):
        uc = UpdateChecker()
        available, info = uc.check_for_update()
        if not info:
            Popup(title="Update", content=Label(text="Could not check for updates."), size_hint=(0.6,0.3)).open()
            return
        if available:
            notes = info.get("notes","")
            apk_url = info.get("apk_url","")
            content = BoxLayout(orientation="vertical")
            content.add_widget(Label(text=f"New version: {info.get('latest_version')}"))
            content.add_widget(Label(text=f"Notes: {notes}"))
            dl_btn = Button(text="Download APK", size_hint_y=None, height=40)
            def dl(a):
                dest = "downloaded_update.apk"
                ok = uc.download_apk(apk_url, dest)
                if ok:
                    Popup(title="Downloaded", content=Label(text=f"APK downloaded to {dest}"), size_hint=(0.6,0.3)).open()
                else:
                    Popup(title="Error", content=Label(text="Failed to download APK"), size_hint=(0.6,0.3)).open()
            dl_btn.bind(on_release=dl)
            content.add_widget(dl_btn)
            Popup(title="Update Available", content=content, size_hint=(0.8,0.6)).open()
        else:
            Popup(title="Update", content=Label(text="App is up-to-date."), size_hint=(0.6,0.3)).open()

from kivy.uix.boxlayout import BoxLayout as KBox
class SBPIApp(App):
    def build(self):
        root = KBox(orientation="vertical")
        # Header
        header = BoxLayout(size_hint_y=None, height=50, padding=6)
        header.add_widget(Label(text="[b]SBPI[/b] Industry Log", markup=True))
        root.add_widget(header)
        tp = MainApp()
        root.add_widget(tp)
        return root

if __name__ == "__main__":
    SBPIApp().run()

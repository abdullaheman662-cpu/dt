import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import sqlite3
import re
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).parent; DB=ROOT/'flavorhub.db'; ASSETS=ROOT/'assets'
NAVY='#10243A'; NAVY2='#173B5E'; RED='#8F1734'; RED2='#B42342'; WHITE='#FFFFFF'; BG='#F2F5F9'; TEXT='#24364B'; MUTED='#68788B'; GREEN='#18794E'; GOLD='#E7A23B'
#list
SEED=[('Classic Beef Burger','Burgers','Juicy beef patty with lettuce and house sauce',850,'burger'),('Chicken Tikka Pizza','Pizza','Chicken tikka, onion and melted cheese',1550,'pizza'),('Creamy Alfredo Pasta','Pasta','Creamy white sauce, herbs and parmesan',980,'pasta'),('Loaded Fries','Appetizers','Crispy fries with cheese sauce',480,'fries'),('Chocolate Cake','Desserts','Rich chocolate cake with chocolate drizzle',450,'cake'),('Crispy Chicken Burger','Burgers','Crispy chicken, lettuce and mayo',720,'chicken_burger'),('Margherita Pizza','Pizza','Tomato, mozzarella and basil',1250,'margherita'),('Club Sandwich','Sandwiches','Triple-layer chicken sandwich',780,'sandwich'),('Chicken Nuggets','Appetizers','Golden chicken nuggets with dip',550,'nuggets'),('Fresh Lemonade','Drinks','Fresh lemon and mint',250,'lemonade'),('Cold Coffee','Drinks','Chilled coffee with milk',380,'coffee'),('Cheesecake Slice','Desserts','Creamy classic cheesecake',520,'cheesecake')]

class App:
 def __init__(self,root):
  self.root=root; root.title('FlavorHub Restaurant Management'); root.geometry('1280x800'); root.minsize(980,650); root.configure(bg=BG)
  #queue,stack,dictionary
  self.queue=deque(); self.preparing=None; self.cart={}; self.cart_undo_stack=[]; self.images={}; self.customer_name_var=tk.StringVar(root); self.customer_phone_var=tk.StringVar(root); self.order_kind_var=tk.StringVar(root,value='Dine-in'); self.order_details_var=tk.StringVar(root); self.payment_method_var=tk.StringVar(root,value='Cash on Delivery'); self.custom_allergies_var=tk.StringVar(root); self.chosen_item_var=tk.StringVar(root); self.item_quantity_var=tk.IntVar(root,value=1); self.allergy_vars={a:tk.BooleanVar(root,value=False) for a in ['Peanuts','Tree nuts','Dairy','Eggs','Wheat / Gluten','Soy','Fish','Shellfish']}; self.setup_db(); self.reload_queue(); self.style(); self.shell(); self.page('Dashboard')
  #stack-save state
 def save_cart_state(self):
  # Stack (LIFO): save the current cart before each change so the last change can be undone.
  self.cart_undo_stack.append({name: item.copy() for name, item in self.cart.items()})
  if len(self.cart_undo_stack)>30: self.cart_undo_stack.pop(0)
  #stack-undo
 def undo_cart_change(self):
  if not self.cart_undo_stack:
   messagebox.showinfo('Nothing to undo','There are no recent cart changes to undo.'); return False
  self.cart=self.cart_undo_stack.pop()
  return True
 def connect(self): return sqlite3.connect(DB)
 def setup_db(self):
  with self.connect() as c:
   c.execute('CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY,name TEXT UNIQUE,category TEXT,description TEXT,price REAL,photo TEXT,available INTEGER DEFAULT 1)')
   c.execute('CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer TEXT,phone TEXT,kind TEXT,details TEXT,subtotal REAL,fee REAL,total REAL,status TEXT,created TEXT,payment_method TEXT DEFAULT \"N/A\",payment_status TEXT DEFAULT \"Not Applicable\")')
   # Add payment columns to databases created by earlier versions.
   order_columns=[r[1] for r in c.execute('PRAGMA table_info(orders)').fetchall()]
   if 'payment_method' not in order_columns: c.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'N/A'")
   if 'payment_status' not in order_columns: c.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Not Applicable'")
   c.execute('CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY,order_id INTEGER,name TEXT,qty INTEGER,price REAL)')
   c.execute('CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,customer TEXT,rating INTEGER,review TEXT,order_id INTEGER,created TEXT)')
   if c.execute('SELECT COUNT(*) FROM menu').fetchone()[0]==0: c.executemany('INSERT INTO menu(name,category,description,price,photo) VALUES(?,?,?,?,?)',SEED)
   # Correct only the photo assignment for existing menu items too.
   for item_name, photo_key in [('Crispy Chicken Burger','chicken_burger'),('Margherita Pizza','margherita'),('Club Sandwich','sandwich'),('Chicken Nuggets','nuggets'),('Fresh Lemonade','lemonade'),('Cold Coffee','coffee'),('Cheesecake Slice','cheesecake')]:
    c.execute('UPDATE menu SET photo=? WHERE name=?',(photo_key,item_name))
    #queue-pending order loads
 def reload_queue(self):
  with self.connect() as c: self.queue=deque(r[0] for r in c.execute("SELECT id FROM orders WHERE status='Pending' ORDER BY id")); r=c.execute("SELECT id FROM orders WHERE status='Preparing' ORDER BY id LIMIT 1").fetchone(); self.preparing=r[0] if r else None
 def style(self):
  s=ttk.Style(); s.theme_use('clam'); s.configure('Treeview',rowheight=30,font=('Segoe UI',10),background=WHITE,fieldbackground=WHITE,foreground=TEXT); s.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),background='#E4EAF2',foreground=NAVY); s.configure('TEntry',padding=7); s.configure('TCombobox',padding=7)
 def shell(self):
  self.side=tk.Frame(self.root,bg=NAVY,width=220); self.side.pack(side='left',fill='y'); self.side.pack_propagate(False)
  tk.Label(self.side,text='FLAVOR',fg=WHITE,bg=NAVY,font=('Segoe UI',21,'bold')).pack(anchor='w',padx=22,pady=(24,0)); tk.Label(self.side,text='HUB  /  RESTAURANT',fg='#E7A6B5',bg=NAVY,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=23,pady=(0,24))
  self.nav={}
  for name,icon in [('Dashboard','▦'),('Menu','♨'),('New Order','＋'),('Orders','▤'),('Completed Orders','✓'),('Cancelled Orders','×'),('Customer Reviews','☆'),('Menu Management','☷'),('Sales Report','▥'),('Settings / About','⚙')]:
   b=tk.Button(self.side,text=f'  {icon}    {name}',anchor='w',bg=NAVY,fg='#E7EDF5',activebackground=RED,activeforeground=WHITE,relief='flat',bd=0,font=('Segoe UI',10),padx=12,pady=12,cursor='hand2',command=lambda n=name:self.page(n)); b.pack(fill='x',padx=8,pady=2); b.bind('<Enter>',lambda e,w=b: w.configure(bg=RED2) if w!=self.active_nav else None); b.bind('<Leave>',lambda e,w=b: w.configure(bg=NAVY) if w!=self.active_nav else None); self.nav[name]=b
  tk.Label(self.side,text='GOOD FOOD.\nGOOD MOOD.',fg='#A9BDD0',bg=NAVY,font=('Georgia',15,'italic'),justify='center').pack(side='bottom',pady=28)
  self.body=tk.Frame(self.root,bg=BG); self.body.pack(side='left',fill='both',expand=True)
  top=tk.Frame(self.body,bg=WHITE,height=78); top.pack(fill='x'); top.pack_propagate(False)
  self.title=tk.Label(top,text='FlavorHub Restaurant',bg=WHITE,fg=NAVY,font=('Segoe UI',20,'bold')); self.title.pack(side='left',padx=25,pady=14)
  tk.Label(top,text='RESTAURANT MANAGEMENT  •  PKR',bg=WHITE,fg=MUTED,font=('Segoe UI',9,'bold')).pack(side='right',padx=24)
  self.area=tk.Frame(self.body,bg=BG); self.area.pack(fill='both',expand=True,padx=22,pady=18); self.active_nav=self.nav['Dashboard']
 def clear(self):
  for w in self.area.winfo_children(): w.destroy()
 def page(self,name):
  self.current=name; self.title.config(text='FlavorHub Restaurant  /  '+name); self.active_nav=self.nav[name]
  for n,b in self.nav.items(): b.configure(bg=RED if n==name else NAVY,fg=WHITE if n==name else '#E7EDF5')
  self.clear(); {'Dashboard':self.dashboard,'Menu':self.menu_page,'New Order':self.order_page,'Orders':lambda:self.orders_page(False),'Completed Orders':lambda:self.orders_page(True),'Cancelled Orders':self.cancelled_page,'Customer Reviews':self.reviews_page,'Menu Management':self.management_page,'Sales Report':self.sales_page,'Settings / About':self.about_page}[name]()
 def heading(self,text): tk.Label(self.area,text=text,bg=BG,fg=NAVY,font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(0,12))
 def stat(self,parent,label,value,color):
  f=tk.Frame(parent,bg=WHITE,highlightbackground='#D9E1EA',highlightthickness=1,padx=15,pady=14); tk.Label(f,text=label.upper(),bg=WHITE,fg=MUTED,font=('Segoe UI',8,'bold')).pack(anchor='w'); tk.Label(f,text=str(value),bg=WHITE,fg=color,font=('Segoe UI',20,'bold')).pack(anchor='w',pady=(5,0)); return f
 def stats(self):
  with self.connect() as c:
   n=c.execute("SELECT COUNT(*) FROM orders WHERE status!='Cancelled'").fetchone()[0]; p=c.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]; prep=c.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Preparing','Ready')").fetchone()[0]; done=c.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]; sales=c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='Completed'").fetchone()[0]
  return n,p,prep,done,sales
 def dashboard(self):
  n,p,pr,d,s=self.stats(); row=tk.Frame(self.area,bg=BG); row.pack(fill='x',pady=(0,14))
  for a,b,col in [('Total Orders',n,NAVY2),('Pending Orders',p,RED),('Preparing / Ready',pr,GOLD),('Completed Orders',d,GREEN),('Total Sales',f'Rs. {s:,.0f}',NAVY2)]: self.stat(row,a,b,col).pack(side='left',fill='x',expand=True,padx=(0,8))
  banner=tk.Frame(self.area,bg=NAVY,padx=24,pady=22); banner.pack(fill='x',pady=(0,15)); tk.Label(banner,text='WELCOME TO FLAVORHUB',bg=NAVY,fg='#F4C6D0',font=('Segoe UI',9,'bold')).pack(anchor='w'); tk.Label(banner,text='Fresh food. Great taste. Better together.',bg=NAVY,fg=WHITE,font=('Segoe UI',21,'bold')).pack(anchor='w',pady=4); tk.Label(banner,text='A smarter way to manage your restaurant, kitchen and customers.',bg=NAVY,fg='#D5E0EA',font=('Segoe UI',10)).pack(anchor='w'); tk.Button(banner,text='+  CREATE NEW ORDER',bg=RED,fg=WHITE,relief='flat',font=('Segoe UI',10,'bold'),padx=16,pady=9,command=lambda:self.page('New Order')).pack(anchor='w',pady=(14,0))
  self.heading('Popular Food Items'); row=tk.Frame(self.area,bg=BG); row.pack(fill='x')
  for name,price,photo in [('Classic Beef Burger',850,'burger'),('Chicken Tikka Pizza',1550,'pizza'),('Creamy Alfredo Pasta',980,'pasta'),('Loaded Fries',480,'fries'),('Chocolate Cake',450,'cake')]:
   f=tk.Frame(row,bg=WHITE,highlightbackground='#D9E1EA',highlightthickness=1); f.pack(side='left',fill='both',expand=True,padx=(0,8)); self.food_image(photo,(f,)); tk.Label(f,text=name,bg=WHITE,fg=NAVY,font=('Segoe UI',9,'bold'),wraplength=130).pack(anchor='w',padx=8,pady=(7,2)); tk.Label(f,text=f'Rs. {price:,}',bg=WHITE,fg=RED,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=8,pady=(0,10))
  # Fill the space left by Recent Orders with a compact promotional panel.
  promo=tk.Frame(self.area,bg=WHITE,highlightbackground='#D9E1EA',highlightthickness=1); promo.pack(fill='x',pady=(18,0))
  accent=tk.Frame(promo,bg=RED,width=8); accent.pack(side='left',fill='y')
  content=tk.Frame(promo,bg=WHITE,padx=20,pady=15); content.pack(side='left',fill='both',expand=True)
  tk.Label(content,text='FLAVORHUB SPECIAL',bg=WHITE,fg=RED,font=('Segoe UI',9,'bold')).pack(anchor='w')
  tk.Label(content,text='Good food, made for your mood.',bg=WHITE,fg=NAVY,font=('Segoe UI',16,'bold')).pack(anchor='w',pady=(3,2))
  tk.Label(content,text='Choose your favourites, combine multiple items, and let our kitchen take care of the rest.',bg=WHITE,fg=MUTED,font=('Segoe UI',10),wraplength=760,justify='left').pack(anchor='w')
  tk.Button(promo,text='＋  START AN ORDER',bg=NAVY,fg=WHITE,activebackground=RED,activeforeground=WHITE,relief='flat',font=('Segoe UI',10,'bold'),padx=16,pady=12,cursor='hand2',command=lambda:self.page('New Order')).pack(side='right',padx=20,pady=20)
 def food_image(self,photo,parent):
  frame=parent[0] if isinstance(parent,tuple) else parent
  try:
   from PIL import Image,ImageTk
   path=ASSETS/f'{photo}.jpg'; im=Image.open(path); im.thumbnail((220,110)); ph=ImageTk.PhotoImage(im); self.images[str(path)+str(id(frame))]=ph; tk.Label(frame,image=ph,bg=WHITE).pack(fill='x')
  except Exception: tk.Label(frame,text={'burger':'🍔','pizza':'🍕','pasta':'🍝','fries':'🍟','cake':'🍰'}.get(photo,'🍽'),bg=WHITE,font=('Segoe UI Emoji',34)).pack(fill='x',pady=10)
 def table(self,parent,cols,height=12):
  wrap=tk.Frame(parent,bg=BG); wrap.pack(fill='both',expand=True); t=ttk.Treeview(wrap,columns=cols,show='headings',height=height)
  for col in cols:
   t.heading(col,text=col,anchor='center')
   width=130; anchor='center'
   if col=='Description': width=300; anchor='w'
   elif col in ('Name','Category','Address / Table','Details'): width=175; anchor='w'
   elif col in ('Availability','Status','Type','Price','Price PKR','Total PKR','Sales Value PKR','Rating','ID','Order ID'): width=105
   elif col in ('Items','Review'): width=230; anchor='w'
   t.column(col,width=width,anchor=anchor,stretch=True)
  sy=ttk.Scrollbar(wrap,orient='vertical',command=t.yview); sx=ttk.Scrollbar(wrap,orient='horizontal',command=t.xview); t.configure(yscrollcommand=sy.set,xscrollcommand=sx.set); t.grid(row=0,column=0,sticky='nsew'); sy.grid(row=0,column=1,sticky='ns'); sx.grid(row=1,column=0,sticky='ew'); wrap.rowconfigure(0,weight=1); wrap.columnconfigure(0,weight=1); return t
 def menu_page(self):
  self.heading('Our Menu')
  bar=tk.Frame(self.area,bg=BG); bar.pack(fill='x',pady=(0,10))
  cat=tk.StringVar(value='All')
  ttk.Combobox(bar,textvariable=cat,values=['All','Burgers','Pizza','Pasta','Sandwiches','Appetizers','Desserts','Drinks'],state='readonly',width=16).pack(side='left')
  tk.Button(bar,text='FILTER MENU',bg=RED,fg=WHITE,relief='flat',padx=12,pady=8,command=lambda:refresh()).pack(side='left',padx=8)
  tk.Button(bar,text='+ ADD ITEM',bg=NAVY,fg=WHITE,relief='flat',padx=12,pady=8,command=lambda:self.page('Menu Management')).pack(side='right')
  # Scrollable food-card menu with pictures, prices, quantity and Add to Cart.
  outer=tk.Frame(self.area,bg=BG); outer.pack(fill='both',expand=True)
  canvas=tk.Canvas(outer,bg=BG,highlightthickness=0,yscrollincrement=30)
  scroll=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview)
  canvas.configure(yscrollcommand=scroll.set)
  scroll.pack(side='right',fill='y'); canvas.pack(side='left',fill='both',expand=True)
  cards=tk.Frame(canvas,bg=BG); window=canvas.create_window((0,0),window=cards,anchor='nw')
  # Keep the scrollable area in sync with the full card grid.
  cards.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
  canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
  self.menu_canvas=canvas
  def menu_mousewheel(event):
   # Scroll only when the pointer is inside the Menu canvas, not on other pages.
   cv=getattr(self,'menu_canvas',None)
   if self.current!='Menu' or cv is None or not cv.winfo_exists(): return
   x,y=cv.winfo_pointerx(),cv.winfo_pointery()
   left,top=cv.winfo_rootx(),cv.winfo_rooty()
   if left <= x < left+cv.winfo_width() and top <= y < top+cv.winfo_height():
    if getattr(event,'num',None)==4: cv.yview_scroll(-3,'units')
    elif getattr(event,'num',None)==5: cv.yview_scroll(3,'units')
    else:
     delta=getattr(event,'delta',0)
     if delta: cv.yview_scroll(-max(1,int(abs(delta)/120))*(1 if delta>0 else -1),'units')
    return 'break'
  # bind_all lets the wheel work over pictures, cards, and labels too.
  canvas.bind_all('<MouseWheel>',menu_mousewheel)
  canvas.bind_all('<Button-4>',menu_mousewheel)
  canvas.bind_all('<Button-5>',menu_mousewheel)
  def add_to_cart(name,price,qty_var):
   try: amount=int(qty_var.get())
   except (ValueError,tk.TclError): messagebox.showwarning('Quantity','Enter a quantity from 1 to 50.'); return
   if amount<1 or amount>50: messagebox.showwarning('Quantity','Enter a quantity from 1 to 50.'); return
   self.save_cart_state(); self.cart.setdefault(name,{'price':price,'qty':0}); self.cart[name]['qty']+=amount
   messagebox.showinfo('Added to cart',f'{name} × {amount} added to your cart.\nYou can add more items or open New Order to confirm the order.')
  def refresh():
   for w in cards.winfo_children(): w.destroy()
   #list-database results
   with self.connect() as c: rows=c.execute('SELECT name,category,description,price,photo,available FROM menu ORDER BY category,name').fetchall()
   rows=[r for r in rows if (cat.get()=='All' or r[1]==cat.get()) and r[5]]
   for i,(name,category,desc,price,photo,available) in enumerate(rows):
    card=tk.Frame(cards,bg=WHITE,highlightbackground='#D9E1EA',highlightthickness=1,padx=10,pady=10)
    card.grid(row=i//3,column=i%3,sticky='nsew',padx=7,pady=7)
    # Use a consistent picture size on menu cards to prevent uneven rows.
    try:
     from PIL import Image,ImageTk,ImageOps
     path=ASSETS/f'{photo}.jpg'
     im=Image.open(path).convert('RGB')
     im=ImageOps.fit(im,(220,110))
     ph=ImageTk.PhotoImage(im)
     self.images['menu_'+str(path)+str(id(card))]=ph
     tk.Label(card,image=ph,bg=WHITE,width=220,height=110).pack(fill='x')
    except Exception:
     tk.Label(card,text={'burger':'🍔','pizza':'🍕','pasta':'🍝','fries':'🍟','cake':'🍰'}.get(photo,'🍽'),bg=WHITE,font=('Segoe UI Emoji',34),height=3).pack(fill='x')
    tk.Label(card,text=name,bg=WHITE,fg=NAVY,font=('Segoe UI',11,'bold'),wraplength=220,justify='left').pack(anchor='w',pady=(8,3))
    tk.Label(card,text=desc,bg=WHITE,fg=MUTED,font=('Segoe UI',9),wraplength=220,justify='left').pack(anchor='w',pady=(0,5))
    tk.Label(card,text=f'Rs. {price:,.0f}',bg=WHITE,fg=RED,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,7))
    qrow=tk.Frame(card,bg=WHITE); qrow.pack(fill='x',pady=(0,7))
    tk.Label(qrow,text='Quantity',bg=WHITE,fg=TEXT,font=('Segoe UI',9)).pack(side='left')
    q=tk.IntVar(value=1); ttk.Spinbox(qrow,from_=1,to=50,textvariable=q,width=5).pack(side='right')
    tk.Button(card,text='＋  ADD TO CART',bg=NAVY,fg=WHITE,activebackground=RED,activeforeground=WHITE,relief='flat',font=('Segoe UI',9,'bold'),padx=8,pady=8,cursor='hand2',command=lambda n=name,p=price,v=q:add_to_cart(n,p,v)).pack(fill='x')
   for col in range(3): cards.columnconfigure(col,weight=1,uniform='menu')
   if not rows: tk.Label(cards,text='No available items in this category.',bg=BG,fg=MUTED,font=('Segoe UI',11)).grid(row=0,column=0,padx=20,pady=20,sticky='w')
  refresh()
 def order_page(self):
  self.heading('Create a New Customer Order')
  # Keep the complete New Order form inside a vertical canvas so it scrolls on shorter screens.
  order_wrap=tk.Frame(self.area,bg=BG); order_wrap.pack(fill='both',expand=True)
  order_canvas=tk.Canvas(order_wrap,bg=BG,highlightthickness=0)
  order_scroll=ttk.Scrollbar(order_wrap,orient='vertical',command=order_canvas.yview)
  order_canvas.configure(yscrollcommand=order_scroll.set)
  order_scroll.pack(side='right',fill='y'); order_canvas.pack(side='left',fill='both',expand=True)
  content=tk.Frame(order_canvas,bg=BG); canvas_window=order_canvas.create_window((0,0),window=content,anchor='nw')
  content.bind('<Configure>',lambda e:order_canvas.configure(scrollregion=order_canvas.bbox('all')))
  order_canvas.bind('<Configure>',lambda e:order_canvas.itemconfigure(canvas_window,width=e.width))
  def order_wheel(event):
   if getattr(event,'delta',0): order_canvas.yview_scroll(-int(event.delta/120) if abs(event.delta)>=120 else (-1 if event.delta>0 else 1),'units')
   elif getattr(event,'num',None)==4: order_canvas.yview_scroll(-3,'units')
   elif getattr(event,'num',None)==5: order_canvas.yview_scroll(3,'units')
  order_canvas.bind('<MouseWheel>',order_wheel); order_canvas.bind('<Button-4>',order_wheel); order_canvas.bind('<Button-5>',order_wheel)
  def order_wheel_global(event):
   if self.current=='New Order' and order_canvas.winfo_exists(): return order_wheel(event)
  self.root.bind_all('<MouseWheel>',order_wheel_global,add='+'); self.root.bind_all('<Button-4>',order_wheel_global,add='+'); self.root.bind_all('<Button-5>',order_wheel_global,add='+')
  split=tk.Frame(content,bg=BG); split.pack(fill='both',expand=True); left=tk.Frame(split,bg=WHITE,padx=18,pady=16); left.pack(side='left',fill='both',expand=True,padx=(0,12)); right=tk.Frame(split,bg=WHITE,padx=18,pady=16); right.pack(side='left',fill='both',expand=True)
  def field(parent,label): tk.Label(parent,text=label,bg=WHITE,fg=TEXT,font=('Segoe UI',9,'bold')).pack(anchor='w'); e=ttk.Entry(parent); e.pack(fill='x',pady=(3,9)); return e
  tk.Label(left,text='CUSTOMER DETAILS',bg=WHITE,fg=NAVY,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,10)); name=field(left,'Customer name'); name.configure(textvariable=self.customer_name_var); phone=field(left,'Phone number'); phone.configure(textvariable=self.customer_phone_var)
  def name_keycheck(event):
   if event.keysym in ('BackSpace','Delete','Left','Right','Home','End','Tab','Return','Shift_L','Shift_R','Control_L','Control_R') or event.state & 4: return
   if event.char and not (event.char.isalpha() or event.char in " '-"):
    messagebox.showerror('Invalid customer name','Customer name can contain letters, spaces, apostrophes or hyphens only. Numbers are not allowed.')
    return 'break'
  def phone_keycheck(event):
   if event.keysym in ('BackSpace','Delete','Left','Right','Home','End','Tab','Return','Shift_L','Shift_R','Control_L','Control_R') or event.state & 4: return
   if event.char and not event.char.isdigit():
    messagebox.showerror('Invalid phone number','Phone number must contain digits only and start with 03 or 92.')
    return 'break'
   if event.char:
    current=phone.get(); start=phone.index(tk.SEL_FIRST) if phone.selection_present() else phone.index(tk.INSERT); end=phone.index(tk.SEL_LAST) if phone.selection_present() else start
    candidate=current[:start]+event.char+current[end:]
    if len(candidate)>=1 and candidate[0] not in ('0','9'):
     messagebox.showerror('Invalid phone number','Phone number must start with 03 or 92.')
     return 'break'
    if len(candidate)>=2 and not (candidate.startswith('03') or candidate.startswith('92')):
     messagebox.showerror('Invalid phone number','Phone number must start with 03 or 92.')
     return 'break'
    if len(candidate)>11:
     messagebox.showerror('Phone number too long','Phone number must be exactly 11 digits. Extra digits are not allowed.')
     return 'break'
  name.bind('<KeyPress>',name_keycheck); phone.bind('<KeyPress>',phone_keycheck)
  kind=self.order_kind_var; tk.Label(left,text='Order type',bg=WHITE,fg=TEXT).pack(anchor='w'); kind_box=ttk.Combobox(left,textvariable=kind,values=['Dine-in','Delivery','Self Pickup'],state='readonly'); kind_box.pack(fill='x',pady=(3,9)); details_label=tk.Label(left,text='Table number',bg=WHITE,fg=TEXT,font=('Segoe UI',9,'bold')); details_label.pack(anchor='w'); details=ttk.Entry(left,textvariable=self.order_details_var); details.pack(fill='x',pady=(3,9)); pickup_note=tk.Label(left,text='Self Pickup: collect your order from the FlavorHub restaurant. Enter an estimated arrival time (e.g. 10 minutes or 5:30 PM).',bg=WHITE,fg=MUTED,font=('Segoe UI',9),wraplength=420,justify='left'); payment=self.payment_method_var; payment_label=tk.Label(left,text='Payment method (Delivery only)',bg=WHITE,fg=TEXT); payment_box=ttk.Combobox(left,textvariable=payment,values=['Cash on Delivery','Online Payment'],state='readonly');
  # New uniqueness feature: customers can flag allergies before adding items.
  allergy_names=['Peanuts','Tree nuts','Dairy','Eggs','Wheat / Gluten','Soy','Fish','Shellfish']
  allergy_vars=self.allergy_vars
  allergy_box=tk.LabelFrame(left,text='SMART ALLERGY ALERT (Optional)',bg=WHITE,fg=RED,font=('Segoe UI',9,'bold'),padx=8,pady=6)
  allergy_box.pack(fill='x',pady=(2,8))
  tk.Label(allergy_box,text='Select listed allergies, or type any other allergy below. You can enter multiple custom allergies separated by commas.',bg=WHITE,fg=TEXT,font=('Segoe UI',8),wraplength=400,justify='left').pack(anchor='w',pady=(0,4))
  allergy_grid=tk.Frame(allergy_box,bg=WHITE); allergy_grid.pack(fill='x')
  for ai,allergen in enumerate(allergy_names):
   tk.Checkbutton(allergy_grid,text=allergen,variable=allergy_vars[allergen],bg=WHITE,fg=TEXT,activebackground=WHITE,selectcolor=WHITE,font=('Segoe UI',8)).grid(row=ai//2,column=ai%2,sticky='w',padx=(0,8))
  tk.Label(allergy_box,text='Other allergy (type it here):',bg=WHITE,fg=TEXT,font=('Segoe UI',8,'bold')).pack(anchor='w',pady=(5,2))
  custom_allergies=ttk.Entry(allergy_box,textvariable=self.custom_allergies_var); custom_allergies.pack(fill='x')
  tk.Label(allergy_box,text='Alerts are a precaution only. Menu ingredient data may be incomplete; always verify ingredients and cross-contact with restaurant staff.',bg=WHITE,fg=MUTED,font=('Segoe UI',8),wraplength=400,justify='left').pack(anchor='w',pady=(4,0))
  allergen_map={
   'Classic Beef Burger':{'Wheat / Gluten','Dairy','Eggs','Soy'},
   'Chicken Tikka Pizza':{'Wheat / Gluten','Dairy'},
   'Creamy Alfredo Pasta':{'Wheat / Gluten','Dairy','Eggs'},
   'Loaded Fries':{'Dairy'},
   'Chocolate Cake':{'Wheat / Gluten','Dairy','Eggs','Soy'},
   'Crispy Chicken Burger':{'Wheat / Gluten','Dairy','Eggs','Soy'},
   'Margherita Pizza':{'Wheat / Gluten','Dairy'},
   'Club Sandwich':{'Wheat / Gluten','Dairy','Eggs'},
   'Chicken Nuggets':{'Wheat / Gluten','Eggs','Soy'},
   'Fresh Lemonade':set(),
   'Cold Coffee':{'Dairy'},
   'Cheesecake Slice':{'Wheat / Gluten','Dairy','Eggs'}
  }
  #set-allerging matching
  def allergy_warning(food_names):
   selected={a for a,v in allergy_vars.items() if v.get()}
   custom=[a.strip() for a in custom_allergies.get().split(',') if a.strip()]
   if not selected and not custom: return False
   matched=[]; uncertain=[]
   with self.connect() as c:
    descriptions={n:(d or '') for n,d in c.execute('SELECT name,description FROM menu').fetchall()}
   for food_name in food_names:
    known=allergen_map.get(food_name)
    found=(selected & known) if known is not None else set()
    if found: matched.append((food_name,sorted(found)))
    desc=descriptions.get(food_name,'').casefold()
    custom_found=[a for a in custom if a.casefold() in desc or a.casefold() in food_name.casefold()]
    if custom_found: matched.append((food_name,['custom allergy: '+', '.join(custom_found)]))
    # Custom allergies cannot be reliably ruled out using a short menu description.
    if custom and not custom_found: uncertain.append(food_name)
    if known is None and not found: uncertain.append(food_name)
   if matched or uncertain:
    lines=[]
    for food_name,found in matched: lines.append(f"{food_name}: possible match for {', '.join(found)}")
    for food_name in dict.fromkeys(uncertain): lines.append(f'{food_name}: ingredients have not been fully verified against your custom allergy/allergies')
    lines.append('Please verify the full ingredients and cross-contact with restaurant staff. Do not rely on this alert as a safety guarantee.')
    return not messagebox.askyesno('Smart Allergy Alert','\n'.join(lines)+'\n\nAdd/continue with these items anyway?')
   return False
  def payment_visibility(*args):
   if kind.get()=='Delivery':
    details_label.config(text='Delivery address'); payment_label.pack(anchor='w'); payment_box.pack(fill='x',pady=(3,9)); pickup_note.pack_forget()
   elif kind.get()=='Self Pickup':
    details_label.config(text='Approximate pickup time'); payment_label.pack_forget(); payment_box.pack_forget(); pickup_note.pack(anchor='w',pady=(0,8))
   else:
    details_label.config(text='Table number'); payment_label.pack_forget(); payment_box.pack_forget(); pickup_note.pack_forget()
  kind.trace_add('write',payment_visibility); payment_visibility(); tk.Label(left,text='Select food item',bg=WHITE,fg=TEXT).pack(anchor='w')
  with self.connect() as c: items=c.execute('SELECT name,price FROM menu WHERE available=1 ORDER BY name').fetchall()
  tk.Label(left,text='Add items one by one. Set a separate quantity for each item; all added items stay in the same order.',bg=WHITE,fg=MUTED,font=('Segoe UI',9),wraplength=420,justify='left').pack(anchor='w',pady=(2,4))
  chosen=self.chosen_item_var; item_box=ttk.Combobox(left,textvariable=chosen,values=[f'{n} — Rs. {p:,.0f}' for n,p in items],state='readonly'); item_box.pack(fill='x',pady=5)
  qty=self.item_quantity_var; qrow=tk.Frame(left,bg=WHITE); qrow.pack(fill='x',pady=4); tk.Label(qrow,text='Quantity for this item:',bg=WHITE,fg=TEXT).pack(side='left'); ttk.Spinbox(qrow,from_=1,to=50,textvariable=qty,width=6).pack(side='left',padx=8)
  summary=tk.Listbox(right,height=13,bg='#F4F6FA',relief='flat',font=('Segoe UI',10),exportselection=False); summary.pack(fill='both',expand=True); total=tk.Label(right,text='Subtotal Rs. 0  |  Delivery Rs. 0  |  Total Rs. 0',bg=WHITE,fg=NAVY,font=('Segoe UI',10,'bold'),wraplength=380); total.pack(anchor='w',pady=10)
  def update():
   summary.delete(0,'end'); sub=sum(x['price']*x['qty'] for x in self.cart.values())
   for n,x in self.cart.items(): summary.insert('end',f"{n}  × {x['qty']}  =  Rs. {x['price']*x['qty']:,.0f}")
   fee=200 if kind.get()=='Delivery' and self.cart else 0; total.config(text=f'Subtotal Rs. {sub:,.0f}  |  Delivery Rs. {fee}  |  Total Rs. {sub+fee:,.0f}')
  update()
  def add():
   if not chosen.get(): messagebox.showwarning('Select item','Choose one food item first.'); return
   try: amount=int(qty.get())
   except (ValueError,tk.TclError): messagebox.showwarning('Quantity','Enter a quantity from 1 to 50.'); return
   if amount<1 or amount>50: messagebox.showwarning('Quantity','Enter a quantity from 1 to 50.'); return
   n=chosen.get().split(' — Rs.')[0]
   if allergy_warning([n]): return
   price=next(p for a,p in items if a==n); self.save_cart_state(); self.cart.setdefault(n,{'price':price,'qty':0}); self.cart[n]['qty']+=amount; update(); chosen.set(''); qty.set(1)
  def remove():
   s=summary.curselection()
   if s: self.save_cart_state(); del self.cart[list(self.cart)[s[0]]]; update()
   else: messagebox.showwarning('Select item','Select an item in the order summary to remove it.')
  tk.Button(left,text='ADD SELECTED ITEM + QUANTITY',bg=NAVY,fg=WHITE,relief='flat',padx=10,pady=9,command=add).pack(anchor='w',pady=9)
  adjust=tk.Frame(right,bg=WHITE); adjust.pack(fill='x',pady=(0,8))
  def adjust_quantity(change):
   sel=summary.curselection()
   if not sel: messagebox.showwarning('Select item','Select an item in the order summary first.'); return
   n=list(self.cart)[sel[0]]; new_qty=self.cart[n]['qty']+change; self.save_cart_state()
   if new_qty<=0: del self.cart[n]
   else: self.cart[n]['qty']=new_qty
   update()
  tk.Button(adjust,text='−  ONE LESS',bg='#E5EAF1',fg=NAVY,relief='flat',padx=8,pady=7,command=lambda:adjust_quantity(-1)).pack(side='left',padx=(0,6))
  tk.Button(adjust,text='+  ONE MORE',bg='#E5EAF1',fg=NAVY,relief='flat',padx=8,pady=7,command=lambda:adjust_quantity(1)).pack(side='left',padx=(0,6))
  tk.Button(adjust,text='REMOVE ITEM',bg=RED,fg=WHITE,relief='flat',padx=8,pady=7,command=remove).pack(side='left',padx=(0,6))
  def undo_cart():
   if self.undo_cart_change(): update()
  tk.Button(adjust,text='↶ UNDO LAST CHANGE',bg='#DCE8F3',fg=NAVY,relief='flat',padx=8,pady=7,command=undo_cart).pack(side='left')
  def confirm():
   customer=name.get().strip(); ph=phone.get().strip(); det=details.get().strip()
   if not customer or not ph or not self.cart or not det: messagebox.showerror('Missing details','Enter name, phone, the required field for the selected order type, and at least one item.'); return
   if allergy_warning(list(self.cart)): return
   if kind.get()=='Dine-in' and not det.isdigit(): messagebox.showerror('Table number','For Dine-in, enter a table number using digits only. Delivery address and pickup time are not accepted here.'); return
   if kind.get()=='Delivery':
    if len(det)<8 or not any(ch.isalpha() for ch in det) or re.fullmatch(r'(?i)\s*\d+\s*(min|mins|minute|minutes|hours?|hrs?)\s*',det) or re.fullmatch(r'\s*\d{1,2}:\d{2}\s*(am|pm)?\s*',det,re.I): messagebox.showerror('Delivery address','Enter a valid delivery address, not a time. Include your street/area or house/building details.'); return
   if kind.get()=='Self Pickup' and not (re.fullmatch(r'\s*\d{1,3}\s*(min|mins|minute|minutes)\s*',det,re.I) or re.fullmatch(r'\s*\d{1,2}:\d{2}\s*(am|pm)?\s*',det,re.I)):
    messagebox.showerror('Pickup time','Enter an approximate time, e.g. 10 minutes or 5:30 PM. Text/address is not accepted here.'); return
   if not any(ch.isalpha() for ch in customer) or any(ch.isdigit() for ch in customer): messagebox.showerror('Customer name','Name must contain letters only; numbers are not allowed.'); return
   if len(ph)!=11 or not ph.isdigit() or not (ph.startswith('03') or ph.startswith('92')): messagebox.showerror('Invalid phone number','Phone number must contain exactly 11 digits and start with 03 or 92 (for example, 03001234567 or 923001234567).'); phone.focus_set(); return
   sub=sum(x['price']*x['qty'] for x in self.cart.values()); fee=200 if kind.get()=='Delivery' else 0; pay_method=payment.get() if kind.get()=='Delivery' else 'Not Applicable'; pay_status=('Paid (Demo)' if pay_method=='Online Payment' else 'Pay on Delivery') if kind.get()=='Delivery' else 'Not Applicable'
   # Ask for confirmation before saving the order, to prevent accidental clicks.
   dialog=tk.Toplevel(self.root); dialog.title('Confirm Your Order'); dialog.configure(bg=WHITE); dialog.resizable(False,False); dialog.transient(self.root)
   tk.Label(dialog,text='CONFIRM ORDER?',bg=WHITE,fg=NAVY,font=('Segoe UI',14,'bold')).pack(padx=26,pady=(22,8))
   tk.Label(dialog,text=f'Customer: {customer}\nItems: {sum(x["qty"] for x in self.cart.values())} total\nOrder type: {kind.get()}\nPayment: {pay_method}\nTotal: Rs. {sub+fee:,.0f}',bg=WHITE,fg=TEXT,font=('Segoe UI',10),justify='left').pack(padx=26,pady=(0,18),anchor='w')
   actions=tk.Frame(dialog,bg=WHITE); actions.pack(fill='x',padx=20,pady=(0,20))
   def save_order():
    if pay_method=='Online Payment':
     if not messagebox.askyesno('Demo Online Payment','This project does not connect to a real payment gateway. Record this demo online payment as successful?'):
      return
    with self.connect() as c:
     cur=c.execute('INSERT INTO orders(customer,phone,kind,details,subtotal,fee,total,status,created,payment_method,payment_status) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(customer,ph,kind.get(),det,sub,fee,sub+fee,'Pending',datetime.now().strftime('%Y-%m-%d %H:%M'),pay_method,pay_status)); oid=cur.lastrowid; c.executemany('INSERT INTO order_items(order_id,name,qty,price) VALUES(?,?,?,?)',[(oid,n,x['qty'],x['price']) for n,x in self.cart.items()])
    self.reload_queue(); self.cart={}; self.cart_undo_stack.clear(); dialog.destroy(); messagebox.showinfo('Order confirmed',f'Order #{oid}\nCustomer: {customer}\nPhone: {ph}\nPayment: {pay_method} ({pay_status})\nTotal: Rs. {sub+fee:,.0f}\nStatus: Pending (FIFO queue)'); self.page('Orders')
   tk.Button(actions,text='CONFIRM ORDER FOR ME',bg=GREEN,fg=WHITE,relief='flat',padx=12,pady=9,command=save_order).pack(side='left',padx=(0,8))
   tk.Button(actions,text='CANCEL',bg='#E5EAF1',fg=NAVY,relief='flat',padx=18,pady=9,command=dialog.destroy).pack(side='left')
   # Center the confirmation dialog on the screen after its size is known.
   dialog.update_idletasks()
   dw, dh = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
   sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
   dialog.geometry(f'{dw}x{dh}+{max(0,(sw-dw)//2)}+{max(0,(sh-dh)//2)}')
   dialog.grab_set(); dialog.focus_force()
  def clear_order_form():
   if not messagebox.askyesno('Clear New Order','Clear all entered order information and remove all items from the current cart?'):
    return
   self.customer_name_var.set('')
   self.customer_phone_var.set('')
   self.order_kind_var.set('Dine-in')
   self.order_details_var.set('')
   self.payment_method_var.set('Cash on Delivery')
   self.custom_allergies_var.set('')
   self.chosen_item_var.set('')
   self.item_quantity_var.set(1)
   for allergy_var in self.allergy_vars.values():
    allergy_var.set(False)
   self.cart.clear()
   self.cart_undo_stack.clear()
   update()
  tk.Button(right,text='CONFIRM ORDER  →',bg=RED,fg=WHITE,relief='flat',font=('Segoe UI',11,'bold'),padx=15,pady=12,command=confirm).pack(fill='x',pady=(0,8))
  tk.Button(right,text='CLEAR NEW ORDER',bg='#E5EAF1',fg=NAVY,activebackground='#D5DFEA',relief='flat',font=('Segoe UI',10,'bold'),padx=15,pady=10,command=clear_order_form).pack(fill='x')
 def orders_page(self,completed=False):
  self.heading('Completed Orders' if completed else 'Order Queue & Kitchen Workflow'); controls=tk.Frame(self.area,bg=BG); controls.pack(fill='x',pady=(0,10)); t=self.table(self.area,('ID','Customer','Phone','Type','Address / Table','Items','Total PKR','Payment Method','Payment Status','Queue Position','Status'),12)
  def refresh():
   t.delete(*t.get_children()); query="SELECT id,customer,phone,kind,details,total,payment_method,payment_status,status FROM orders WHERE status='Completed' ORDER BY id DESC" if completed else "SELECT id,customer,phone,kind,details,total,payment_method,payment_status,status FROM orders WHERE status IN ('Pending','Preparing','Ready','Out for Delivery') ORDER BY id ASC"
   with self.connect() as c:
    rows=c.execute(query).fetchall()
    pending_ids=[r[0] for r in c.execute("SELECT id FROM orders WHERE status='Pending' ORDER BY id").fetchall()]
    for oid,cu,ph,ki,de,tot,pm,ps,st in rows:
     its=', '.join(f'{n} x{q}' for n,q in c.execute('SELECT name,qty FROM order_items WHERE order_id=?',(oid,)))
     if st=='Pending': position=f'#{pending_ids.index(oid)+1} in queue' if oid in pending_ids else 'Waiting'
     elif st=='Preparing': position='Preparing now'
     elif st=='Ready': position='Ready - awaiting customer'
     elif st=='Out for Delivery': position='Out for delivery'
     else: position='—'
     t.insert('','end',values=(oid,cu,ph,ki,de,its,f'{tot:,.0f}',pm,ps,position,st))
  def selected():
   s=t.selection()
   if not s: messagebox.showwarning('Select order','Select an order first.'); return None
   return t.item(s[0],'values')
  def prepare():
   self.reload_queue()
   # FIFO applies only while an order is being prepared.
   # As soon as it is marked Ready, the next Pending order may start preparing.
   with self.connect() as c: blocker=c.execute("SELECT id,status FROM orders WHERE status='Preparing' ORDER BY id LIMIT 1").fetchone()
   if blocker:
    messagebox.showwarning('FIFO queue',f'Order #{blocker[0]} is still Preparing. Mark it Ready before preparing the next order.'); return
   while self.queue:
    oid=self.queue[0]
    with self.connect() as c: r=c.execute("SELECT status FROM orders WHERE id=?",(oid,)).fetchone()
    if r and r[0]=='Pending':
     with self.connect() as c: c.execute("UPDATE orders SET status='Preparing' WHERE id=?",(oid,))
     self.preparing=oid; self.queue.popleft(); break
    self.queue.popleft()
   else: messagebox.showinfo('Queue empty','There are no pending orders to prepare.'); return
   self.page('Orders')
  def ready():
   v=selected()
   if not v:return
   if v[10]!='Preparing': messagebox.showwarning('Not preparing','Choose the order currently marked Preparing.'); return
   with self.connect() as c:c.execute("UPDATE orders SET status='Ready' WHERE id=?",(v[0],))
   if self.preparing==int(v[0]):self.preparing=None
   self.page('Orders')
  def serve_dine_in():
   v=selected()
   if not v:return
   if v[3]!='Dine-in' or v[10]!='Ready': messagebox.showwarning('Wrong order type','Only a Dine-in order marked Ready can be served to the table.'); return
   with self.connect() as c:c.execute("UPDATE orders SET status='Completed' WHERE id=?",(v[0],))
   messagebox.showinfo('Order served',f'Order #{v[0]} has been served to the customer.'); self.page('Orders')
  def pickup_done():
   v=selected()
   if not v:return
   if v[3]!='Self Pickup' or v[10]!='Ready': messagebox.showwarning('Wrong order type','Only a Self Pickup order marked Ready can be marked Picked Up.'); return
   with self.connect() as c:c.execute("UPDATE orders SET status='Completed' WHERE id=?",(v[0],))
   messagebox.showinfo('Picked Up',f'Order #{v[0]} has been picked up by the customer.'); self.page('Orders')
  def rider_left():
   v=selected()
   if not v:return
   if v[3]!='Delivery' or v[10]!='Ready': messagebox.showwarning('Wrong order type','This is not a Delivery order. Only a Delivery order marked Ready can be sent with the rider.'); return
   with self.connect() as c:c.execute("UPDATE orders SET status='Out for Delivery' WHERE id=?",(v[0],))
   messagebox.showinfo('Rider dispatched',f'Rider has left with order #{v[0]}.'); self.page('Orders')
  def delivered():
   v=selected()
   if not v:return
   if v[3]!='Delivery' or v[10]!='Out for Delivery': messagebox.showwarning('Wrong order type or status','Only a Delivery order already marked Out for Delivery can be marked delivered.'); return
   with self.connect() as c:c.execute("UPDATE orders SET status='Completed' WHERE id=?",(v[0],))
   messagebox.showinfo('Delivered',f'Order #{v[0]} has been delivered.'); self.page('Orders')
  def cancel():
   v=selected()
   if not v:return
   if v[10] not in ('Pending','Preparing','Ready'):
    messagebox.showwarning('Cannot cancel','Only Pending, Preparing or Ready orders can be cancelled here.'); return
   if messagebox.askyesno('Cancel order',f'Cancel order #{v[0]}?'):
    with self.connect() as c:c.execute("UPDATE orders SET status='Cancelled' WHERE id=?",(v[0],))
    self.reload_queue();self.page('Orders')
  if not completed:
   for label,color,cmd in [('PREPARE NEXT (FIFO)',NAVY,prepare),('MARK READY',GOLD,ready),('MARK SERVED (DINE-IN)',GREEN,serve_dine_in),('MARK PICKED UP',GREEN,pickup_done),('RIDER LEFT (DELIVERY)',NAVY2,rider_left),('MARK DELIVERED',GREEN,delivered),('CANCEL ORDER',RED,cancel)]:tk.Button(controls,text=label,bg=color,fg=WHITE,relief='flat',padx=8,pady=8,command=cmd).pack(side='left',padx=(0,5))
   tk.Label(controls,text=f'Pending: {len(self.queue)}  •  Preparing: {("#"+str(self.preparing)) if self.preparing else "None"}',bg=BG,fg=NAVY,font=('Segoe UI',10,'bold')).pack(side='right')
  refresh()
  if completed:
   def clear_completed():
    if not messagebox.askyesno('Clear completed orders','Delete all completed orders from this list?'): return
    with self.connect() as c:
     ids=[r[0] for r in c.execute("SELECT id FROM orders WHERE status='Completed'").fetchall()]
     if ids:
      c.executemany('DELETE FROM order_items WHERE order_id=?',[(oid,) for oid in ids]); c.executemany('DELETE FROM reviews WHERE order_id=?',[(oid,) for oid in ids]); c.executemany("DELETE FROM orders WHERE id=? AND status='Completed'",[(oid,) for oid in ids])
    refresh()
   tk.Button(controls,text='CLEAR COMPLETED ORDERS',bg=RED,fg=WHITE,relief='flat',padx=12,pady=8,command=clear_completed).pack(side='left')
 def cancelled_page(self):
  self.heading('Cancelled Orders & Online Refunds'); controls=tk.Frame(self.area,bg=BG); controls.pack(fill='x',pady=(0,10)); t=self.table(self.area,('ID','Customer','Phone','Type','Details','Total PKR','Payment Method','Payment Status','Date'),13)
  with self.connect() as c:
   for r in c.execute("SELECT id,customer,phone,kind,details,total,payment_method,payment_status,created FROM orders WHERE status='Cancelled' ORDER BY id DESC"):t.insert('','end',values=(r[0],r[1],r[2],r[3],r[4],f'{r[5]:,.0f}',r[6],r[7],r[8]))
  def mark_refunded():
   selected=t.selection()
   if not selected: messagebox.showwarning('Select order','Select a cancelled order first.'); return
   values=t.item(selected[0],'values'); oid=int(values[0]); method=values[6]; status=values[7]
   if method!='Online Payment' or status not in ('Paid (Demo)','Refund Pending'):
    messagebox.showinfo('Refund not needed','Refund is available only for cancelled orders paid online and not already refunded. Cash on Delivery orders do not need a refund.'); return
   if messagebox.askyesno('Confirm Refund',f'Mark the online payment for order #{oid} as refunded?\n\nNote: this records the refund in the project; it does not transfer real money.'):
    with self.connect() as c:c.execute("UPDATE orders SET payment_status='Refunded' WHERE id=? AND status='Cancelled'",(oid,))
    self.page('Cancelled Orders')
  tk.Button(controls,text='MARK ONLINE PAYMENT AS REFUNDED',bg=GREEN,fg=WHITE,relief='flat',padx=12,pady=9,command=mark_refunded).pack(side='left')
  tk.Label(controls,text='For cancelled online-paid orders only',bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(side='left',padx=10)
  def clear_cancelled():
   if not messagebox.askyesno('Clear cancelled orders','Permanently delete all cancelled orders from this list? This cannot be undone.'): return
   with self.connect() as c:
    ids=[r[0] for r in c.execute("SELECT id FROM orders WHERE status='Cancelled'").fetchall()]
    if ids:
     c.executemany('DELETE FROM order_items WHERE order_id=?',[(oid,) for oid in ids]); c.executemany('DELETE FROM reviews WHERE order_id=?',[(oid,) for oid in ids]); c.executemany("DELETE FROM orders WHERE id=? AND status='Cancelled'",[(oid,) for oid in ids])
   self.page('Cancelled Orders')
  tk.Button(controls,text='CLEAR CANCELLED ORDERS',bg=RED,fg=WHITE,relief='flat',padx=12,pady=9,command=clear_cancelled).pack(side='right')
 def management_page(self):
  self.heading('Menu Management')
  form_outer=tk.Frame(self.area,bg=BG); form_outer.pack(fill='x',pady=(0,10))
  form=tk.Frame(form_outer,bg=WHITE,padx=18,pady=14); form.pack(anchor='center')
  vs=[tk.StringVar() for _ in range(4)]
  labels=['Item name','Category','Description','Price PKR']
  widths=[20,18,30,14]
  for i,label in enumerate(labels):
   tk.Label(form,text=label,bg=WHITE,fg=TEXT,font=('Segoe UI',9,'bold')).grid(row=0,column=i,sticky='w',padx=10,pady=(0,4))
   ttk.Entry(form,textvariable=vs[i],width=widths[i]).grid(row=1,column=i,padx=10,pady=(0,4),sticky='ew')
   form.columnconfigure(i,weight=1)
  t=self.table(self.area,('ID','Name','Category','Description','Price','Availability'),10)
  def refresh():
   t.delete(*t.get_children())
   with self.connect() as c:
    for r in c.execute('SELECT id,name,category,description,price,available FROM menu ORDER BY id'):
     t.insert('','end',values=(r[0],r[1],r[2],r[3],f'Rs. {r[4]:,.0f}','Available' if r[5] else 'Unavailable'))
  def add():
   try:
    n,cat,desc,price=[v.get().strip() for v in vs]
    if not n or not cat or not desc or float(price)<0:raise ValueError
    with self.connect() as c:c.execute('INSERT INTO menu(name,category,description,price,photo) VALUES(?,?,?,?,?)',(n,cat,desc,float(price),'burger'))
    [v.set('') for v in vs];refresh()
   except Exception:messagebox.showerror('Cannot add item','Enter a unique name, category, description and valid price.')
  def toggle():
   s=t.selection()
   if s:
    v=t.item(s[0],'values')
    with self.connect() as c:c.execute('UPDATE menu SET available=? WHERE id=?',(0 if v[5]=='Available' else 1,v[0]))
    refresh()
   else: messagebox.showwarning('Select item','Select a menu item first.')
  def delete():
   s=t.selection()
   if s and messagebox.askyesno('Remove item','Remove selected menu item?'):
    with self.connect() as c:c.execute('DELETE FROM menu WHERE id=?',(t.item(s[0],'values')[0],))
    refresh()
   elif not s: messagebox.showwarning('Select item','Select a menu item first.')
  row=tk.Frame(self.area,bg=BG);row.pack(fill='x',pady=8)
  for label,col,fn in [('ADD MENU ITEM',NAVY,add),('TOGGLE AVAILABILITY',NAVY2,toggle),('REMOVE SELECTED',RED,delete)]:tk.Button(row,text=label,bg=col,fg=WHITE,relief='flat',padx=12,pady=8,command=fn).pack(side='left',padx=(0,8))
  refresh()
 def reviews_page(self):
  self.heading('Customer Reviews'); form=tk.Frame(self.area,bg=WHITE,padx=12,pady=12);form.pack(fill='x',pady=(0,10)); name=tk.StringVar();rating=tk.IntVar(value=5);review=tk.StringVar();oid=tk.StringVar()
  for i,(label,var,width) in enumerate([('Customer name',name,18),('Rating 1–5',rating,8),('Review',review,42),('Order ID optional',oid,14)]):tk.Label(form,text=label,bg=WHITE).grid(row=0,column=i,sticky='w',padx=4);(ttk.Combobox(form,textvariable=var,values=[1,2,3,4,5],state='readonly',width=width) if i==1 else ttk.Entry(form,textvariable=var,width=width)).grid(row=1,column=i,padx=4,pady=4)
  t=self.table(self.area,('Customer','Rating','Review','Order ID','Date'),11);stats=tk.Label(self.area,text='',bg=BG,fg=NAVY,font=('Segoe UI',10,'bold'));stats.pack(anchor='w',pady=8)
  def refresh():
   t.delete(*t.get_children())
   with self.connect() as c:
    rows=c.execute('SELECT customer,rating,review,order_id,created FROM reviews ORDER BY id DESC').fetchall();avg=c.execute('SELECT AVG(rating) FROM reviews').fetchone()[0]
   for r in rows:t.insert('','end',values=(r[0],'★'*r[1],r[2],r[3] or '-',r[4]))
   stats.config(text=f'Average rating: {avg:.1f}/5  •  {len(rows)} submitted reviews' if rows else 'No reviews submitted yet — customer feedback will appear here.')
  def submit():
   if not name.get().strip() or not review.get().strip():messagebox.showerror('Missing details','Enter name and review.');return
   try: order=int(oid.get()) if oid.get().strip() else None
   except ValueError:messagebox.showerror('Order ID','Order ID must be numeric.');return
   with self.connect() as c:
    if order and not c.execute('SELECT id FROM orders WHERE id=?',(order,)).fetchone():messagebox.showerror('Order not found','That order ID does not exist.');return
    c.execute('INSERT INTO reviews(customer,rating,review,order_id,created) VALUES(?,?,?,?,?)',(name.get().strip(),int(rating.get()),review.get().strip(),order,datetime.now().strftime('%Y-%m-%d')))
   name.set('');review.set('');oid.set('');refresh()
  def clear_reviews():
   if not messagebox.askyesno('Clear Reviews','Are you sure you want to clear all customer reviews? This cannot be undone.'):return
   with self.connect() as c:
    c.execute('DELETE FROM reviews')
   refresh()
  tk.Button(form,text='SUBMIT REVIEW',bg=RED,fg=WHITE,relief='flat',command=submit,padx=10,pady=7).grid(row=1,column=4,padx=5)
  tk.Button(form,text='CLEAR REVIEWS',bg=NAVY2,fg=WHITE,relief='flat',command=clear_reviews,padx=10,pady=7).grid(row=1,column=5,padx=5)
  refresh()
 def sales_page(self):
  self.heading('Sales Report');n,p,pr,d,s=self.stats();row=tk.Frame(self.area,bg=BG);row.pack(fill='x',pady=(0,14))
  for a,b,col in [('Completed Orders',d,GREEN),('Total Sales',f'Rs. {s:,.0f}',NAVY2),('Pending Orders',p,RED)]:self.stat(row,a,b,col).pack(side='left',fill='x',expand=True,padx=(0,8))
  self.heading('Top 3 Best-Selling Items')
  top=tk.Frame(self.area,bg=BG); top.pack(fill='x',pady=(0,12))
  with self.connect() as c:
   best=c.execute("SELECT i.name,SUM(i.qty),SUM(i.qty*i.price) FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.status='Completed' GROUP BY i.name ORDER BY SUM(i.qty) DESC, i.name LIMIT 3").fetchall()
  if not best: tk.Label(top,text='Complete orders to see your top-selling food items.',bg=WHITE,fg=MUTED,padx=14,pady=14).pack(fill='x')
  else:
   for rank,(name,qty_sold,value) in enumerate(best,1):
    f=tk.Frame(top,bg=WHITE,highlightbackground='#D9E1EA',highlightthickness=1,padx=14,pady=12); f.pack(side='left',fill='both',expand=True,padx=(0,8))
    tk.Label(f,text=f'#{rank} BEST SELLER',bg=WHITE,fg=RED,font=('Segoe UI',9,'bold')).pack(anchor='w')
    tk.Label(f,text=name,bg=WHITE,fg=NAVY,font=('Segoe UI',12,'bold'),wraplength=220).pack(anchor='w',pady=(5,2))
    tk.Label(f,text=f'Quantity sold: {qty_sold}  •  Sales: Rs. {value:,.0f}',bg=WHITE,fg=MUTED,font=('Segoe UI',9),wraplength=240).pack(anchor='w')
  self.heading('All Best-Selling Menu Items');t=self.table(self.area,('Menu Item','Quantity Sold','Sales Value PKR'),12)
  with self.connect() as c:
   for r in c.execute("SELECT i.name,SUM(i.qty),SUM(i.qty*i.price) FROM order_items i JOIN orders o ON o.id=i.order_id WHERE o.status='Completed' GROUP BY i.name ORDER BY SUM(i.qty) DESC"):t.insert('','end',values=(r[0],r[1],f'Rs. {r[2]:,.0f}'))
 def about_page(self):
  self.heading('Settings / About');f=tk.Frame(self.area,bg=WHITE,padx=28,pady=25);f.pack(fill='x');tk.Label(f,text='FLAVORHUB RESTAURANT',bg=WHITE,fg=NAVY,font=('Segoe UI',23,'bold')).pack(anchor='w');tk.Label(f,text='Restaurant Management System',bg=WHITE,fg=RED,font=('Segoe UI',13,'bold')).pack(anchor='w',pady=5);tk.Label(f,text='Built with Python, Tkinter, SQLite and collections.deque.\n\nData Structure: FIFO Queue — each order must reach the customer before the next order is prepared.\n\nOrder types: Dine-in, Delivery and Self Pickup.\n\nCurrency: Pakistani Rupees (PKR)  •  Delivery fee: Rs. 200\nDatabase: flavorhub.db (saved in this project folder)',bg=WHITE,fg=TEXT,justify='left',font=('Segoe UI',11)).pack(anchor='w',pady=12)

if __name__=='__main__':
 root=tk.Tk(); app=App(root); root.mainloop()

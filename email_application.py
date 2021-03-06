import smtplib
import imaplib
import datetime
import email
import os
import io
import re
import PIL
from PIL import ImageTk, Image
import time
import shutil

try:
    import tkinter as tk
    from tkinter import *
    from tkinter import messagebox
    from tkinter import filedialog
except:
    import Tkinter as tk
    from Tkinter import *
    import tkMessageBox
    import tkFileDialog
    from tkFileDialog import askopenfilename

import mimetypes
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText


# Scrollable Frame by Eugene Bakin - https://gist.github.com/EugeneBakin/76c8f9bcec5b390e45df
class VerticalScrollFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)

        # Create a canvas object and a vertical scrollbar
        scrollbar = Scrollbar(self, orient=VERTICAL)
        scrollbar.pack(fill=Y, side=RIGHT, expand=0)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=1)
        scrollbar.config(command=canvas.yview)

        # Reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # Track changes to the canvas and frame width and synch them, also updating scrollbar
        def _configure_interior(event):
            # Update the scrollbar to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

def delete_folders():
    for i in range(len(folderpaths)):
        if os.path.exists(folderpaths[i]):
            shutil.rmtree(folderpaths[i])

    del folderpaths[0:len(folderpaths)]


def on_close():
    #delete_files()
    delete_folders()
    gui.destroy()

def reply(file, emailfrom, subject):
    replyemail = Toplevel()
    replyemail.title("Reply Message")
    Label(replyemail, text="To:").grid(row=0)
    Label(replyemail, text="Subject:").grid(row=1)
    Label(replyemail, text="CC:").grid(row=2)
    Label(replyemail, text="BCC:").grid(row=3)
    Label(replyemail, text="Message:").grid(row=4)

    To = Entry(replyemail, text = emailfrom, width=150)
    To.grid(row=0, column=1)
    To.insert(END, emailfrom)
    To.config(state = DISABLED)
    Subject = Entry(replyemail, text="RE: [%s]" % subject, width=150)
    Subject.grid(row=1, column=1)
    Subject.insert(END, "RE: %s" % subject)
    Subject.config(state = DISABLED)
    CC = Entry(replyemail, width=150)
    CC.grid(row=2, column=1)
    BCC = Entry(replyemail, width=150)
    BCC.grid(row=3, column=1)
    msg = Text(replyemail, bd=5)
    msg.grid(row=6, column=1, stick=E + W + N + S)
    attachment = Entry(replyemail, width=150, state=DISABLED)
    attachment.grid(row=4, column=1)

    msg.insert(INSERT, "\n")

    for i in range(111):
        msg.insert(INSERT, "-")
    msg.insert(INSERT, "\n")

    textfile = io.open(file, 'r', encoding="utf-8")
    email_message = textfile.read()
    textfile.close()  
    msg.insert(END, email_message)

    attach = Button(replyemail, text="Add Attachment", command=lambda: selectAttachment(attachment))
    attach.grid(row=4, column=0)

    detach = Button(replyemail, text="Remove Attachment", command=lambda: removeAttachment(attachment))
    detach.grid(row=5, column=0)

    send = Button(replyemail, text="Send", command=lambda: donothing())
    send.grid(row=7, column=1)

def updateGIF(window, display, gif, num_frames, ind):
    frame = gif[ind]
    ind += 1
    display.configure(image = frame)
    if ind == num_frames:
        ind = 0
    if num_frames < 10:
        delay = num_frames * 10 + (num_frames * 3)
    else:
        delay = num_frames - 10

    window.after(delay, updateGIF, window, display, gif, num_frames, ind)

def display_gif(path):
    title = path.split("\\")[-1]
    gif_img = Toplevel()
    gif_img.title(title)
    im = PIL.Image.open(path)
    width, height = im.size
    gif_img.configure(width = width, height = height)

    # Iterate through the entire GIF
    try:
        while 1:    
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    num_frames = im.tell()
    im.close()
    gif = [PhotoImage(file = path, format = 'gif -index %i' % i) for i in range(num_frames)]
    panel = Label(gif_img)
    panel.pack()
    updateGIF(gif_img, panel, gif, num_frames, 0)

def popup(event, menu):
    try: 
        menu.tk_popup(event.x_root, event.y_root, 0)
    finally:
        menu.grab_release()

def display_email(root, display_region, folderpath, emailfrom, subject):
    try:
        # Clear the display region of any current content
        display_region.config(state = NORMAL)
        display_region.delete("1.0", END)
    except:
        pass

    try:
        replyBttn[-1].destroy()
        del replyBttn[0:len(replyBttn)]
    except:
        pass

    try:
        display_region.tag_remove("instruction")
    except:
        pass

    # Find the path of the folder, any directories the path contains, and any files within the path
    path, dirs, files = next(os.walk(folderpath))        
    # See if the folder contains a textfile
    textfile = []
    for i in range(len(files)):
        file = re.findall(r"[\w_-]+.txt", files[i])
        if len(file) == 1:
            textfile.append(file[0])
    # If there is a textfile, print its contents in the display region
    if len(textfile) == 1:
        filepath = os.path.join(path, str(textfile[0]))
        contents = io.open(filepath, 'r', encoding = "utf-8")
        email_msg = contents.read()
        contents.close()
        display_region.insert(END, email_msg)

    # See if there are any other attachments
    attachments = []
    for i in range(len(files)):
        attch = re.findall(r"[\w\s_-]+.gif|[\w\s_-]+.jpg|[\w\s_-]+.png", files[i], re.I)
        if len(attch) == 1:
            attachments.append(attch)
    # If there are, insert them into the textbox
    if len(attachments) > 0:
        for i in range(len(attachments)):
            attch = re.findall(r"[\w\s_-]+.jpg|[\w\s_-]+.png", str(attachments[i]))
            if len(attch) == 1:
                attch_path = os.path.join(path, attch[0])
                im = PIL.Image.open(attch_path)
                width, height = im.size     
                display_region.update()     
                dwidth = display_region.winfo_width()
                nheight = int((height * dwidth)/width)    # Calculate new height of the image
                newIm = im.resize((dwidth, nheight), PIL.Image.ANTIALIAS)   # Resize the image to fit the display region
                img = ImageTk.PhotoImage(newIm)
                display_region.image_create(END, image = img)
                display_region.image = img
            gifattch = re.findall(r"[\w\s_-]+.gif", files[i], re.I)
            if len(gifattch) == 1:
                attch_path = os.path.join(path, str(gifattch[0]))
                im = PIL.Image.open(attch_path)
                width, height = im.size     
                display_region.update()     
                dwidth = display_region.winfo_width()
                nheight = int((height * dwidth)/width)   
                newIm = im.resize((dwidth, nheight), PIL.Image.ANTIALIAS)   
                img = ImageTk.PhotoImage(newIm)
                im.close()

                display_region.insert(END, "< Right-Click Image to View GIF >")
                line = display_region.index(tk.INSERT)
                line = line.split(".")[0] + ".0"
                display_region.tag_add("instruction", line, INSERT)
                display_region.tag_config("instruction", background = "yellow", foreground = "red")
                gif_img = Label(display_region, image = img)
                gif_img.image = img
                display_region.window_create(END, window = gif_img)
                # Popup Menu for image
                popup_menu = Menu(gif_img, tearoff = 0)
                popup_menu.add_command(label = "View", command = lambda: display_gif(attch_path))
                gif_img.bind("<ButtonRelease-3>", lambda event: popup(event, popup_menu))

    # Disable the textbox region
    display_region.configure(state = DISABLED)

    # Reply button
    replyBttn.append(Button(root, text = "Reply", command = lambda: reply(filepath, emailfrom, subject)))
    replyBttn[-1].pack(anchor = SE)


def get_emails(root, parent, uname, pword, folder, display_region, label):
    label.config(text = folder)

    # Delete files of previous folder (if any)
    delete_folders()
    del folderpaths[0:len(folderpaths)]
    for i in range(len(buttonlist)):
        buttonlist[i].destroy()
    del buttonlist[0:len(buttonlist)]

    # Clear the display region
    display_region.config(state = NORMAL)
    display_region.delete("1.0", END)
    display_region.config(state = DISABLED)

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(uname, pword)
        mail.list()
        if folder != "Inbox":
            folder = '"[Gmail]/' + folder + '"'
        else:
            pass
        mail.select(folder)

        result, data = mail.uid("search", None, "ALL")
        x = len(data[0].split())

        for i in range(x):
            latest_email_uid = data[0].split()[i]
            typ, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
            raw_email = email_data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            msg = email.message_from_string(raw_email_string)

            # Header Details
            date_tuple = email.utils.parsedate_tz(msg['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                local_message_date = "%s" % (str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
            try:
                email_from = str(email.header.make_header(email.header.decode_header(msg['From'])))
                email_to = str(email.header.make_header(email.header.decode_header(msg['To'])))
                subject = str(email.header.make_header(email.header.decode_header(msg['Subject'])))
                try:
                    email_cc = str(email.header.make_header(email.header.decode_header(msg['CC'])))
                except:
                    email_cc = ""
            except:
                email_from = str(email.Header.make_header(email.header.decode_header(msg['From'])))
                email_to = str(email.Header.make_header(email.header.decode_header(msg['To'])))
                subject = str(email.Header.make_header(email.header.decode_header(msg['Subject'])))
                try:
                    email_cc = str(email.Header.make_header(email.header.decode_header(msg['CC'])))
                except:
                    email_cc = ""

            path = os.path.dirname(os.path.abspath(__file__)) 

            # Body Details
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    newpath = os.path.join(path, "email_" + str(i))

                    if not os.path.exists(newpath):                     # Creates a folder for the email
                        os.makedirs(newpath)
                    folderpaths.append(newpath)                         # Add folder to the list of folders created for the email
                    file_name = "email_" + str(i) + ".txt"
                    filepath = os.path.join(newpath, file_name)

                    output_file = io.open(filepath, 'w', encoding = "utf-8")
                    if email_cc == "":
                        output_file.write("From: %s\nTo: %s\nDate: %s\nSubject: %s\n\nBody: \n\n%s" % (
                           email_from, email_to, local_message_date, subject, body.decode('utf-8')))
                    else:
                        output_file.write("From: %s\nTo: %s\nCC: %s\nDate: %s\nSubject: %s\n\nBody: \n\n%s" % (
                           email_from, email_to, email_cc, local_message_date, subject, body.decode('utf-8')))
                    output_file.close()

                    if folder == "Inbox":
                        buttonlist.append(Button(parent, text = "%s\n%s" % (email_from, subject), 
                                                    padx = 5, pady = 5, command = lambda i=i: display_email(root, display_region, 
                                                                                                            folderpaths[i], email_from, subject)))
                    elif folder == '"[Gmail]/Sent Mail"':
                        buttonlist.append(Button(parent, text = "To: %s\n%s" % (email_to, subject),
                                                    padx = 5, pady = 5, command = lambda i=i: display_email(root, display_region,
                                                                                                            folderpaths[i], email_to, subject)))
                    buttonlist[-1].pack(side=BOTTOM, fill=X)
                else:
                    continue

            # Create file for attachment if any
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()
                if part.get_content_type() == "image/jpeg":
                    pattern = re.compile(".jpg", re.I)                    
                    match = pattern.search(filename)
                    if not match:
                        filename = filename + ".jpg"
                elif part.get_content_type() == "image/gif":
                    pattern = re.compile(".gif", re.I)
                    match = pattern.search(filename)
                    if not match:
                        filename = filename + ".gif"
                else:
                    pass

                att_path = os.path.join(path, "email_" + str(i), filename)

                if not os.path.isfile(att_path):
                    fp = open(att_path, 'wb')
                    fp.write(part.get_payload(decode = True))
                    fp.close()

    except Exception as e:
        print(str(e))

def sendingemail(frame, connection, uname, to, subject, cc, bcc, body, attch):
    msg = MIMEMultipart()
    msg["From"] = uname
    msg["To"] = to
    msg["Subject"] = subject
    msg['CC'] = ", ".join(cc)
    msg.attach(MIMEText(body, "plain"))

    if attch != "":
        path = attch.split("\\")
        ctype, encoding = mimetypes.guess_type(attch)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        if maintype == "text":
            fp = open(attch)
            attachment = MIMEText(fp.read(), _subtype=subtype)
            fp.close()
        elif maintype == "image":
            fp = open(attch, "rb")
            attachment = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
        else:
            fp = open(attch, "rb")
            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(fp.read())
            fp.close()
            encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=path[-1])
        msg.attach(attachment)
    else:
        pass

    recipients = [to] + cc + bcc
    connection.sendmail(uname, recipients, msg.as_string())
    frame.destroy()

    title = "Success"
    msgbox = "Your E-mail has been sent!"
    try:
        tkMessageBox.showinfo(title, msgbox)
    except:
        messagebox.showinfo(title, msgbox)

def selectAttachment(entrybox):
    try:
        filepath = askopenfilename()
    except:
        filepath = filedialog.askopenfilename()
    entrybox.config(state=NORMAL)
    entrybox.delete(0, END)
    entrybox.insert(END, filepath)
    entrybox.config(state=DISABLED)

def removeAttachment(entrybox):
    entrybox.config(state=NORMAL)
    entrybox.delete(0, END)
    entrybox.config(state=DISABLED)

def newemail(connection, uname):
    writeemail = Toplevel()
    writeemail.title("New Message")
    Label(writeemail, text="To:").grid(row=0)
    Label(writeemail, text="Subject:").grid(row=1)
    Label(writeemail, text="CC:").grid(row=2)
    Label(writeemail, text="BCC:").grid(row=3)
    Label(writeemail, text="Message:").grid(row=4)

    To = Entry(writeemail, width=150)
    To.grid(row=0, column=1)
    Subject = Entry(writeemail, width=150)
    Subject.grid(row=1, column=1)
    CC = Entry(writeemail, width=150)
    CC.grid(row=2, column=1)
    BCC = Entry(writeemail, width=150)
    BCC.grid(row=3, column=1)
    msg = Text(writeemail, bd=5)
    msg.grid(row=6, column=1, stick=E + W + N + S)
    attachment = Entry(writeemail, width=150, state=DISABLED)
    attachment.grid(row=4, column=1)

    attach = Button(writeemail, text="Add Attachment", command=lambda: selectAttachment(attachment))
    attach.grid(row=4, column=0)

    detach = Button(writeemail, text="Remove Attachment", command=lambda: removeAttachment(attachment))
    detach.grid(row=5, column=0)

    send = Button(writeemail, text="Send",
                    command=lambda: sendingemail(writeemail, connection, uname, To.get(), Subject.get(),
                                              CC.get().split(", "), BCC.get().split(", "), msg.get("1.0", END), attachment.get()), width=15)
    send.grid(row=7, column=1)

def logoutBtn(connection, window):
    delete_folders()
    connection.quit()
    window.pack_forget()
    login_screen()

def create_menubar(parent, connection, uname):
    # Logout button
    logout_button = Button(parent, text="Logout", command=lambda: logoutBtn(connection, parent))
    logout_button.pack(anchor=NE)

    # New Message button
    new_button = Button(parent, text="New", command=lambda: newemail(connection, uname))
    new_button.pack(anchor=NW, side=LEFT)

def init_layout(connection, uname, pword, folder):
    window = Frame(gui, height=400, width=600)

    # Menu Bar
    create_menubar(window, connection, uname)

    # Folders
    frame = LabelFrame(window, height=600, width=100, text="Folders", font="16")
    frame.pack(side=LEFT)
    folders = Listbox(frame, font="12", height=600, width=10)
    folders.insert(END, "Inbox")
    folders.insert(END, "Sent Mail")
    folders.pack(side=LEFT, fill=Y)

    # List of emails
    email_list_frame = LabelFrame(window, height=600, width=200, font="16")
    email_list_frame.pack(side=LEFT, fill=Y)
    email_list = VerticalScrollFrame(email_list_frame)
    email_list.pack(fill=BOTH, expand=1)

    # Email display region
    email = LabelFrame(window, height=600, width=500, text="E-Mail", font="16")
    email.pack()
    scrollbar = Scrollbar(email, orient=VERTICAL)
    scrollbar.pack(side=RIGHT, fill=Y, expand=0)
    display_region = Text(email, wrap=WORD, yscrollcommand=scrollbar.set, state=DISABLED)
    display_region.pack(side=LEFT, fill=BOTH, expand=1)
    scrollbar.config(command=display_region.yview)

    # Reply Button
    folders.bind("<Double-Button-1>", lambda e: get_emails(window, email_list.interior,
                                                            uname, pword, folders.get(ACTIVE), display_region, email_list_frame))
    get_emails(window, email_list.interior, uname, pword, "Inbox", display_region, email_list_frame)

    window.pack()


def loginError():
    # Create a message box informing of incorrect login credentials
    title = "Error"
    msg = "Invalid username or password. Try again."
    try:
        messagebox.showerror(title, msg)
    except:
        tkMessageBox.showerror(title, msg)


def loginSuccess(connection, frame, uname, pword):
    try:
        frame.destroy()
    except Exception as e:
        print(str(e))
    init_layout(connection, uname, pword, "Inbox")


def login(frame, uname, pword):
    # Connecting to server
    server = smtplib.SMTP("smtp.gmail.com: 587")
    server.ehlo()
    server.starttls()
    server.ehlo()
    try:
        server.login(uname, pword)
        loginSuccess(server, frame, uname, pword)
    except Exception as e:
        print(str(e))
        loginError()


def login_screen():
    gui.geometry("600x400")
    # Login screen
    window = Frame(gui, bg="pink", height=400, width=600)
    window.pack()

    # Username
    Label(window, text="Username: ", font="stencil", bg="white", fg="black").place(x=175, y=125)
    username = Entry(window, bd=5)
    username.place(x=300, y=125)

    # Password
    Label(window, text="Password: ", font="stencil", bg="white", fg="black").place(x=175, y=175)
    password = Entry(window, bd=5, show="*")
    password.place(x=300, y=175)

    # Login button
    logBttn = Button(window, font="stencil", text="Login",
                    command=lambda: login(window, username.get(), password.get()))
    logBttn.place(x=270, y=250)

    username.bind('<Return>', lambda e: login(window, username.get(), password.get()))
    password.bind('<Return>', lambda e: login(window, username.get(), password.get()))


# Create GUI window
gui = tk.Tk()
gui.minsize(600, 400)
gui.maxsize(1121, 517)
gui.title("Email Application")

gui.protocol("WM_DELETE_WINDOW", lambda: on_close())

folderpaths = []
buttonlist = []
replyBttn = []

login_screen()
gui.mainloop()

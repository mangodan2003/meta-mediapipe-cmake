try:
    import dearpygui.dearpygui as dpg
except:
    dpg = None
from random import randrange
from threading import Thread, Lock
from time import sleep

mutex = Lock()

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class LogContext:
    def __init__(self, parent, context_str, list_manager=False):
        self._inhibited = parent.inhibited if parent is not None else False
        self._context_str = context_str if parent is None else f"{parent.context_str}::{context_str}"
        self._label = context_str
        self._child_contexts = {}
        self._list_manager = list_manager
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def context_str(self):
        return self._context_str
    
    @property
    def child_contexts_count(self):
        return self._child_contexts.count()
    
    def new(self, context_str, list_manager=False):
        child_context = get_log_manager().new(context_str, self, list_manager=list_manager)
        if child_context._context_str not in self._child_contexts:
            self._child_contexts[child_context.context_str] = child_context
        return child_context
        
    def info(self, str):
        if not self._inhibited:
            print(f"INFO : {self.context_str} => {str}")
            #sleep (0.1)

    def warning(self, str):
        if not self._inhibited:
            print(f"{color.YELLOW}WARNING{color.END} : {self.context_str} => {str}")

    @property
    def inhibited(self):
        return self._inhibited
    
    @inhibited.setter
    def inhibited(self, inhibited):
        #print(f"Set inihibit for {self.context_str} to {inhibited}")
        self._inhibited = inhibited
        if dpg is None:
            return
        # Update the UI
        tag = f"log_context::{self.context_str}-checkbox"
        with mutex:
            dpg.set_value(tag, not inhibited)


class LogManager:
    def __init__(self):
        self._contexts = {}

    def new(self, context_str, parent=None, list_manager=False):
        with mutex:
            if context_str in self._contexts:
                return self._contexts[context_str]
            context = LogContext(parent, context_str, list_manager=list_manager)
            self._contexts[context_str] = context
            self.add_log_context_to_ui(context)
            return context
    

    def add_log_context_to_ui(self, context):
        if dpg is None:
            return
        context_parts = context.context_str.split("::")


        log_context_depth = 0
        running_tag = "log_context"
        for p in context_parts:
            parent = running_tag
            running_tag = running_tag + "::" + p

            if not dpg.does_item_exist(running_tag):
                dpg.add_collapsing_header(label=f"{p} - {running_tag}", tag=running_tag, parent=parent, default_open=True, indent=5)
                #dpg.add_text(p, parent=dpg.last_item())


            log_context_depth += 1

        tag = running_tag + "-checkbox"
        value = not context.inhibited
        if not dpg.does_item_exist(tag):
            with dpg.group(parent=running_tag, horizontal=True):
                dpg.add_checkbox(label="Self", default_value=value, callback=check_box_toggled, user_data=context, tag=tag)
                dpg.add_button(label="Set Children", callback=on_set_children, user_data=context, tag=f"{tag}-set-children")
                dpg.add_button(label="Clear Children", callback=on_clear_children, user_data=context, tag=f"{tag}-clear-children")
                dpg.add_button(label="Set Siblings", callback=on_set_siblings, user_data=context, tag=f"{tag}-set-siblings")
                dpg.add_button(label="Clear Siblings", callback=on_clear_siblings, user_data=context, tag=f"{tag}-clear-siblings")


    def set_inhibit_for_children_of(self, context_str, inhibit):
        for c in self._contexts.values():
            if c.context_str.startswith(context_str):
                c.inhibited = inhibit

    
    def set_inhibit_for_siblings_of(self, context, inhibit):
        parent_context = context.parent.context_str if context.parent is not None else ""
        parent_context_len = len(parent_context)
        for c in self._contexts.values():
            if not c.context_str.startswith(parent_context):
                continue
            unique_part = c.context_str[parent_context_len:]
            decendants = unique_part.split("::")[1:]
            print(f"set_inhibit_for_siblings_of() parent_context: {parent_context}, unique_part: {unique_part}, decendants: {decendants}")
            if len(decendants) > 1:
                   continue
            c.inhibited = inhibit

logging = None
#LogManager()


def get_log_manager():
    global logging
    if logging is None:
        logging = LogManager()
    return logging

def check_box_toggled(sender, app_data, context):
    print(f"Checkbox toggled for log context: {context.context_str}, checked: {app_data}")
    context.inhibited = not app_data

def on_set_children(sender, _, context):
    print(f"on_set_children for log context: {context.context_str}")
    get_log_manager().set_inhibit_for_children_of(context.context_str, False)

def on_clear_children(sender, _, context):
    print(f"on_clear_children for log context: {context.context_str}")
    get_log_manager().set_inhibit_for_children_of(context.context_str, True)

def on_set_siblings(sender, _, context):
    print(f"on_set_siblings for log context: {context.context_str}")
    get_log_manager().set_inhibit_for_siblings_of(context, False)

def on_clear_siblings(sender, _, context):
    print(f"on_clear_siblings for log context: {context.context_str}")
    get_log_manager().set_inhibit_for_siblings_of(context, True)




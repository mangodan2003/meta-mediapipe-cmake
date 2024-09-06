import dearpygui.dearpygui as dpg
from random import randrange
from threading import Thread, Lock
from time import sleep
from pywoodfortreesgui import *


forest_names = [
    "Whispering Pines Forest",
    "Moonshadow Grove",
    "Emerald Canopy Woodlands",
    "Stardust Timberland",
    "Enchanted Thicket",
    "Silverleaf Glade",
    "Crimson Bark Woods",
    "Twilight Birch Forest",
    "Mystic Willow Sanctuary",
    "Frostbite Evergreen Forest"
]
    
n_branches = 0
planks = []

log_forests = None
#logging.new("Forests")
log_branches = None
#logging.new("branches")
log_planks = None
#logging.new("Planks")
log_iterations = None

class IdGenerator:
    def __init__(self):
        self._next_id = 0

    @property
    def next_id(self):
        self._next_id += 1
        return self._next_id

class AbstractPlank:
    next_id = 0
    def __init__(self, log_context):
        id = AbstractPlank.next_id
        AbstractPlank.next_id += 1
        log_context.info(f"A new plank of wood with id {id}!")
        #self.log_context = log_context.new(f"Plank of {self.__class__.__name__}[{id}]")

class Pine(AbstractPlank):
    def __init__(self, log_context):
        super().__init__(log_context)

class Birch(AbstractPlank):
    def __init__(self, log_context):
        super().__init__(log_context)

class Oak(AbstractPlank):
    def __init__(self, log_context):
        super().__init__(log_context)

class AbstractTree(IdGenerator):

    class Branch(IdGenerator):

        class Leaf:
            def __init__(self, branch):
                self._id = branch.next_id
                self._branch = branch
                self._age = 0
                branch.log_context.info(f"New leaf with id {self._id}")
                self.log_context = branch.log_context.new(f"leaf[{self._id}]")

            def iterate(self):
                if self._branch._tree.dead:
                    self.log_context.info("I'm just a ghost")
                else:
                    self.log_context.info("Hi!")

        def __init__(self, tree):
            super().__init__()
            self._tree = tree
            self._id = tree.next_id
            self.log_context = tree.log_context.new(f"branch[{self._id}]")
            tree.log_context.info(f"New tree branch with id {self._id}")
            self._leaves = []

        def iterate(self):
            if len(self._leaves) < 5 and randrange(10) > 8:
                self._leaves.append(AbstractTree.Branch.Leaf(self))

            if self._tree.dead:
                self.log_context.info("I'm just a ghost")
            else:
                self.log_context.info("Hello!")


            for l in self._leaves:
                l.iterate()


    def __init__(self, forest, log_context):
        super().__init__()
        self._id = forest.next_id
        self._name = f"{self._type.__name__}[{self._id}]"
        self.log_context = log_context.new(self.name, list_manager=True)
        self.iteration_log_context = self.log_context.new("iteration")
        log_context.info(f"New tree with id {self._id}")
        self.reset()

    def reset(self):
        self.age = 0
        self.branches = []
        self._diseased = False
        self._felled = False        

    @property
    def dead(self):
        return self._felled or self._diseased


    @property
    def name(self):
        return self._name

    @property
    def cause(self):
        if self._diseased:
            return "died of disease"
        if self._felled:
            return "felled"
        return "unknown"


    def iterate(self):
        self.iteration_log_context.info(f"Running an iteration! age: {self.age}")
        for b in self.branches:
            b.iterate()
        
        # if self.dead:
        #     self.iteration_log_context.info(f"This plot is empty:! {self.cause}")
        #     if  randrange(10) > 8:
        #         self.reset()
        #         self.iteration_log_context.info(f"New tree growing in this plot.")
        #     return
        
        if self.dead:
            self.log_context.info("I'm just a ghost")
        else:
            self.log_context.info("Olla!")


        self.age += 1
        if len(self.branches) < 5 and  randrange(10) > 7:
            self.new_branch()

        if self.age > 10 + randrange(10) and randrange(10) > 8:
            self.felled()

        if((self.age > 20 or randrange(10) > 8) and self._id == 2):
            self.died()

    def felled(self):
        planks.extend([self._type(log_planks) for n in range(0, self.age)])
        self._felled = True

    def died(self):
        self.log_context.info("Died prematurely of disease!!")
        self._diseased = True

    def new_branch(self):
        self.branches.append(AbstractTree.Branch(self))
        global n_branches
        n_branches += 1

    @property
    def is_dead(self):
        return self._dead

class OakTree(AbstractTree):
    def __init__(self, forest, log_context):
        self._type = Oak
        super().__init__(forest, log_context)

class BirchTree(AbstractTree):
    def __init__(self, forest, log_context):
        self._type = Birch
        super().__init__(forest, log_context)

class PineTree(AbstractTree):
    def __init__(self, forest, log_context):
        self._type = Pine
        super().__init__(forest, log_context)

class Forest(IdGenerator):
    def __init__(self, name, log_context):
        super().__init__()
        self.log_context = log_context.new(name)
        self._trees = []
        self.name = name

        log_context.info(f"New Forest \"{name}\", spwaning trees!")
        for t in ((OakTree, self.log_context.new("Oak")), ( BirchTree, self.log_context.new("Birch")),   (PineTree, self.log_context.new("Pine"))):
            for i in range(0, 5):
                self.new_tree(t) 

    def new_tree(self, type):
        self._trees.append(type[0](self, type[1]))


    def iterate(self):
        self.log_context.info("Running an iteration!")
        for t in self._trees:
            t.iterate()
            #if t.is_dead:
            #    self._trees.remove(t)







def run(iterations):

    def doit():
        global log_iterations
        forests = [Forest(f"Forest {forest_names[i]}", log_forests) for i in range(0, 4)]

        forests_str = ""
        for f in forests:
            forests_str += f" {f.name}, "


        for i in range(0, iterations):
            log_iterations.info(f"Iteration {i}")
            for f in forests:
                f.iterate()
            log_branches.info(f"We have grown {n_branches} branches!")
            log_planks.info(f"We have {len(planks)} planks of wood!")
            sleep(0.1)
        


        print("Simulation ended.")

    doit()


def start_logging():
    iterations = int(dpg.get_value("iterations"))
    t = Thread(target=run, args=[iterations])
    t.start()

def main():
    global logging
    global log_forests
    global log_branches
    global log_planks
    global log_iterations

    dpg.create_context()
    dpg.create_viewport(title='Custom Title', width=600, height=300)
    


    with dpg.window(label="Window", tag="Window"):
        dpg.add_collapsing_header(label="Log Contexts:", tag="log_context", default_open=True)
        dpg.add_input_text(label="iterations", default_value=100, tag="iterations")
        dpg.add_button(label="Start", callback=start_logging )

    logging = LogManager()
    log_forests = logging.new("Forests")
    log_branches = logging.new("branches")
    log_planks = logging.new("Planks")
    log_iterations = logging.new("Iterations")

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


main()
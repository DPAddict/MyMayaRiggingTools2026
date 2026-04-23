from Core.MayaWidget import MayaWidget   # import custom base class that works correctly within Maya
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QColorDialog  # imports UI from Qt
import maya.cmds as mc  # imports Maya's Python commands to control the scene
from maya.OpenMaya import MVector  # imports Maya's library, same as the Vector3 in Unity

import importlib  # reloads Pythons built-in library
import Core.MayaUtilities  # imports MayaUtilities 
importlib.reload(Core.MayaUtilities) # imports all the defaluts from Maya Utilities
from Core.MayaUtilities import (CreateCircleControllerForJnt, 
                                CreateBoxControllerForJnt, 
                                CreatePlusController,
                                ConfigureCtrlForJnt,
                                GetObjectPosisiotnAsMVec)

class LimbRigger:  # class that handles the rigging job
    def __init__(self):
        self.nameBase = ""   # create empty string that will hold Limb name
        self.controllerSize = 10   # radius of FK controllers
        self.blendControllerSize = 4  # IKFK switch controller size
        self.controlColorRGB = [0,0,0]   # representing RBG colors

    def SetNameBase(self, newNameBase):   # defines the functions
        self.nameBase = newNameBase
        print(f"Name Base is set to: {self.nameBase}") # print 

    def SetControllerSize(self, newControllerSize): # defines controller size 
        self.controllerSize = newControllerSize

    def SetBlendControllerSize(self, newBlendControllerSize): # defines blend controller size
        self.blendControllerSize = newBlendControllerSize

    def RigLimb(self):   # defines main method to build rig has excess to all earlier variables
        print("Start Rigging!!")
        rootJnt, midJnt, endJnt, = mc.ls(sl=True)  # list selection command
        print(f"Found Root: {rootJnt}, Middle: {midJnt}, End: {endJnt}")

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "Fk_" + self.nameBase, self.controllerSize)  # creates nurb circle for shoulder and names it
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "Fk_" + self.nameBase, self.controllerSize) # nurb circle for elbow names it
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "Fk_" + self.nameBase, self.controllerSize) # nurb circle for wrist name it

        mc.parent(endCtrlGrp, midCtrl)  # parent wrist to elbow
        mc.parent(midCtrlGrp, rootCtrl) # parent elbow to shoulder

        endIkCtrl, endIkCtrlGrp = CreateBoxControllerForJnt(endJnt, "Ik_" + self.nameBase, self.controllerSize) # box controller for IK and name it

        ikFkBlendCtrlPrefix = self.nameBase + "_IKFKBlend" # name for controller 
        ikFkBlendController = CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize) # make plus shape and set size
        ikFkBlendController, ikFkBlendControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False)   # snap plus controller to root joint doesnt contrain to controller
        
        ikFkBlendAttrName = "ikFkBlend" # set a name to ikfk blend
        mc.addAttr(ikFkBlendController, ln=ikFkBlendAttrName, min=0, max=1, k=True)   # a keyable slider to  0 and 1

        ikHandleName = "IKHandleName_" + self.nameBase # creates reverse kinematics
        mc.ikHandle(n=ikHandleName, sj = rootJnt, ee=endJnt, sol="ikRPsolver")   # allows to locate and use pole vector of the limb

        rootJntLoc = GetObjectPosisiotnAsMVec(rootJnt)  # finds x,y,z coordinates of root limb
        endJntLoc = GetObjectPosisiotnAsMVec(endJnt)   # finds x,y,z coords of end of limb


        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0]   # grabs the pole vectors value
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])   # takes pole vectore and sends to mVector constructor 

        poleVecDir.normalize() # unit vecotr that has a length of 1 

        rootToEndVec = endJntLoc - rootJntLoc  # subtracts shoulder and wrist position to get the distance
        rootToEndDist = rootToEndVec.length()  # finds distance the elbow/knee controller should sit

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec/2.0 + poleVecDir * rootToEndDist   # adds the horizontal offset to the vertical offset to create the elbow triangle

        poleVectorCtrlName = "ac_IK_" + self.nameBase + "poleVector"  # creates the elbow pole vector name
        mc.spaceLocator(n=poleVectorCtrlName) # creates a locator for elbow controller

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"  # names group for the elbow
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName)   # creates group for elbow contoller

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3")   # move group to previously calculated coordinates
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName)  # constrains pole vector group to mid joint

        mc.parent(ikHandleName,endIkCtrl)   # makes IK handle child of the wrist box controller
        mc.setAttr(f"{ikHandleName}.v", 0)  # visability on or off

        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{ikHandleName}.ikBlend")  # when 0, IK control off, slider 1, IK sontrol on
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{endIkCtrlGrp}.v")  # connects ik visablity to IK box controller
        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{poleVectorCtrlGrpName}.v")  # connects the pole vector to visabilty

        reverseNodeName = f"{self.nameBase}_reverse"  # name variable 
        mc.createNode("reverse", n=reverseNodeName)  # makes reverse node 

        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{reverseNodeName}.inputX")   # connects 0-1 slider to reverse node 
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v")  # takes output and plugs into FK root group

        orientConstraint = None  # assumes we have not found constraint
        wristConnections = mc.listConnections(endJnt)  # asks maya to show every node plugged into wrist joint
        for connection in wristConnections: # starts a loop 
            if mc.objectType(connection) == "orientConstraint":  # only goes if above is true 
                orientConstraint = connection # store in the variable constraint 
                break  # stop looking 

        mc.connectAttr(f"{ikFkBlendController}.{ikFkBlendAttrName}", f"{orientConstraint}.{endIkCtrl}W1")   # connects 0 to 1 slider to IK weight 
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstraint}.{endCtrl}W0") # when flipped FK has full controll 

        topGrpName = f"{self.nameBase}_rig_grp" # naming string for main folder
        mc.group(n=topGrpName, empty = True) # null folder with no geo

        mc.parent(rootCtrlGrp, topGrpName) # parents FK group to main rig group
        mc.parent(ikFkBlendControllerGrp, topGrpName) # parent IK/FK switch to main rig group
        mc.parent(endIkCtrlGrp, topGrpName) # parents IK writst to main rig group
        mc.parent(poleVectorCtrlGrpName, topGrpName) # parents pole vector in main rig group 

        mc.setAttr(topGrpName + ".overrideEnabled",1) # maya ignores default rules and lets you use master controls 
        mc.setAttr(topGrpName + ".overrideRGBColors",1) # switches from color index to full RGB 
        mc.setAttr(topGrpName + ".overrideColorRGB", self.controlColorRGB[0], self.controlColorRGB[1], self.controlColorRGB[2])  # take color picked by the person and plugs it into said slots 


class LimbRiggerWidget(MayaWidget):  # new class for UI

    def __init__(self):   # runs when window is created 
        super().__init__()  # tells python to run setup code for widget 
        self.setWindowTitle("Limb Rigger")   # text at the top of the window 
        self.rigger = LimbRigger()   # connects buttons to the rigging code 
        self.masterLayout = QVBoxLayout()  # stacks buttons vertically
        self.setLayout(self.masterLayout)  # masterlayout is main organizing system

        self.masterLayout.addWidget(QLabel("Select 3 joints of the limb, from the base to end"))  # noneditable text with instructions 


        self.infoLayout = QHBoxLayout()  # makes horizontal layout 
        self.masterLayout.addLayout(self.infoLayout)  # inside the vertcal mast layout 
        self.infoLayout.addWidget(QLabel("Name Base:"))  # adds a naming field 

        self.nameBaseLineEdit = QLineEdit()  # text imput for naming the limbs 
        self.infoLayout.addWidget(self.nameBaseLineEdit)  # makes button in horizontal layout and next to name base 

        self.setNameBaseBtn = QPushButton("Set Name Base")   # button that is called set name base 
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked)  # button runs when clicked 
        self.infoLayout.addWidget(self.setNameBaseBtn)  # adds button to rright of text box


        self.colorPicker = QPushButton("Color Picker")  # makes button called color picker 
        self.colorPicker.clicked.connect(self.ColorPickerBtnClicked)  # when clicked opens the color wheel
        self.masterLayout.addWidget(self.colorPicker) # button is below the name base section


        self.rigLimbBtn = QPushButton("Rig Limb")  # button to rig limb
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked)  # connects the button and allows rigging when clicked 
        self.masterLayout.addWidget(self.rigLimbBtn)  # button under the select color button 

 
    def SetNameBaseBtnClicked(self):  # hold the info for the color 
        self.rigger.SetNameBase(self.nameBaseLineEdit.text()) # pause script and opens color picker 
    
    def RigLimbBtnClicked(self): # when button labeled rig limb is clicked
        self.rigger.RigLimb()  # does the funciton rig limb 

    
    def ColorPickerBtnClicked(self):    # click and code that holds the color
        pickedColor = QColorDialog().getColor()  # pauses the script opens color picker window 
        self.rigger.controlColorRGB[0] = pickedColor.redF()  # grabs red in picked color
        self.rigger.controlColorRGB[1] = pickedColor.greenF()  # grabs green picked color
        self.rigger.controlColorRGB[2] = pickedColor.blueF()  # grabs blue picked color
        print(self.rigger.controlColorRGB)  # prints RBG 

    def SetControlColor(self, newControlColorRGB):  # overrides old default color 
        self.controlColorRGB = newControlColorRGB



    def GetWidgetHash(self):   
        return "b5921fb4562094613c70a2aa7fb45ae8dabfa8bdad6aad52aa8eef0ffd5b0f06"  


def Run():     # defines run function
    limbRiggerWidget = LimbRiggerWidget()  # becomes object in computer memory
    limbRiggerWidget.show()    # makes window apear 

Run()     # runs code 
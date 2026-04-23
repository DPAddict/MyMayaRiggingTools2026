import maya.cmds as mc
import maya.mel as ml
from maya.OpenMaya import MVector


def ConfigureCtrlForJnt(jnt, ctrlName, doConstraint=True):
   ctrlGrpName = ctrlName + "_grp"
   mc.group(ctrlName, n=ctrlGrpName)

   mc.matchTransform(ctrlGrpName, jnt)
   if doConstraint:
      mc.orientConstraint(ctrlName, jnt)
      

   return ctrlName, ctrlGrpName


# make cross shaped controller / IKFK blend
def CreatePlusController(namePrefix, radius):
   ctrlName =f"ac_{namePrefix}"
  
   ml.eval(f"curve -n {ctrlName}-d 1 -p -1 0 -1 -p -3 0 -1 -p -3 0 1 -p -1 0 1 -p -1 0 3 -p 1 0 3 -p 1 0 1 -p 3 0 1 -p 3 0 -1 -p 1 0 -1 -p 1 0 -3 -p -1 0 -3 -p -1 0 -1 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
   mc.setAttr(f"{ctrlName}.scale")
   mc.makeIdentity(ctrlName, apply = True)


   mc.setAttr(f"{ctrlName}.translateX", lock = True, keyable = False, channelBox = False)
   mc.setAttr(f"{ctrlName}.translateY", lock = True, keyable = False, channelBox = False)
   mc.setAttr(f"{ctrlName}.translateZ", lock = True, keyable = False, channelBox = False)
   

   mc.setAttr(f"{ctrlName}.rotateX", lock = True, keyable = False, channelBox = False)
   mc.setAttr(f"{ctrlName}.rotateY", lock = True, keyable = False, channelBox = False)
   mc.setAttr(f"{ctrlName}.rotateZ", lock = True, keyable = False, channelBox = False)


   mc.setAttr(f"{ctrlName}.scaleX", lock = True, keyable = False, channelBox = False)
   mc.setAttr(f"{ctrlName}.scaleY", lock = True, keyable = False, channelBox = False)
   mc.setAttr(f"{ctrlName}.scaleZ", lock = True, keyable = False, channelBox = False)


   mc.setAttr(f"{ctrlName}.visibility", lock = True, keyable = False, channelBox = False)

   SetCurveLineWidth(ctrlName, 2)

   return ctrlName

  



def CreateCircleControllerForJnt(jnt, namePrefix, radius = 10):
   ctrlName = f"ac_{namePrefix}_{jnt}"
   mc.circle(n=ctrlName, r = radius, nr=(1,0,0))
   
   SetCurveLineWidth(ctrlName, 2)

   return ConfigureCtrlForJnt(jnt, ctrlName)


def CreateBoxControllerForJnt(jnt, namePrefix, size = 10):
   ctrlName = f"ac_{namePrefix}_{jnt}"
   ml.eval(f"curve -n {ctrlName} -d 1 -p -2.645208 2.645208 2.645208 -p 2.645208 2.645208 2.645208 -p 2.645208 2.645208 -2.645208 -p -2.645208 2.645208 -2.645208 -p -2.645208 2.645208 2.645208 -p -2.645208 -2.645208 2.645208 -p 2.645208 -2.645208 2.645208 -p 2.645208 2.645208 2.645208 -p 2.645208 -2.645208 2.645208 -p 2.645208 -2.645208 -2.645208 -p 2.645208 2.645208 -2.645208 -p 2.645208 -2.645208 -2.645208 -p -2.645208 -2.645208 -2.645208 -p -2.645208 2.645208 -2.645208 -p -2.645208 -2.645208 -2.645208 -p -2.645208 -2.645208 2.645208 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 ;")
   mc.setAttr(f"{ctrlName}.scale", size, size, size, type = "double3")

   # Freeze transforms in maya
   mc.makeIdentity(ctrlName, apply = True)

   SetCurveLineWidth(ctrlName, 2)

   return ConfigureCtrlForJnt(jnt, ctrlName)


def GetObjectPosisiotnAsMVec(objectName):
   wsLoc = mc.xform(objectName, t=True, ws=True, q=True)
   return MVector(wsLoc[0], wsLoc[1], wsLoc[2])


def SetCurveLineWidth(curve, newWidth):
   shapes = mc.listRelatives(curve, s = True)
   for shape in shapes:
      mc.setAttr(f"{shape}.lineWidth", newWidth)

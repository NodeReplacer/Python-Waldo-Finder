import numpy,sys
from PIL import Image
import scipy.spatial
from scipy import ndimage
from scipy.ndimage import measurements
from skimage.color import rgb2lab
import scipy.misc

#THIS RUNS IN PYTHON 2
#A TREMENDOUS AMOUNT OF REFERENCE AND CODE WAS USED FROM THE FOLLOWING LOCATION:
#https://github.com/jacobsevart/waldo_uchicago
#SERIOUSLY

# These are some functions that need to be established now.
def plotRectangles(rectangles,maxX,maxY):
	#Draw the "rectangles" (you can see the variable in a function) on a map
	#And merge the touching and overlapping ones into one entity.
	#This'll save SO many overlapping rectangles and make it faster(?) 
	#to calculate our new rectangle section things.
	interMap = numpy.zeros((maxX,maxY))#interMap stands for intermediate map. It is a... map of the intermediate regions of the image and not just the corners and such.
	for key,region in enumerate(rectangles):
		interMap[region] = key #This is important, it establishes the key that is used futher on in the system.
	biggerLabelledRectangles = scipy.ndimage.measurements.label(interMap)[0]
	bigRectangles = scipy.ndimage.measurements.find_objects(biggerLabelledRectangles)

	return (interMap,bigRectangles)
def getLength(x):
	#This breaks down SciPy's bizarre format to get the vertical length of the image. THE ENTIRE IMAGE
	#I can't believe I need to do that but SciPy has some other things I need. So we do it this way.
	return abs(x[0].start - x[0].stop)
def getWidth(x):
	#Same as above with SciPy but this time it's about horizontal length.
	return abs(x[1].start - x[1].stop)
def findColor(labImage,color,delta):
	#Break the input image down into an array. If the pixel is close enough to the colour we are working for then set
	#That shit to true.
	distanceMap = scipy.spatial.distance_matrix(labImage.reshape(maxX * maxY,maxZ),[color])
	return distanceMap < delta

if not len(sys.argv) == 2:
	#Standard system used to figure out if the thing you input was even legal
	#For the entire system to function or not. SUPER IMPORTANT
	print "INPUT FORMAT IS: ",sys.argv[0]," filename.jpg"
	sys.exit()

#So here we load the image
RGBimg = ndimage.io.imread(sys.argv[1])
#This is where we convert it to a LAB image
labImage = rgb2lab(RGBimg)
maxX,maxY,maxZ = labImage.shape

#HOPEFULLY WE FIND THE RED WITH THIS THERE ARE SO MANY DAMN FALSE POSITIVES
redGrid = findColor(labImage,[59,66,38],63)
#GOING FOR THE WHITE
whiteGrid = findColor(labImage,[98,0,0],15)
#HIS HAIR IS BROWNISH BLACK AND NOW WE LOOK FOR THAT
blackGrid = findColor(labImage,[8,2,2],50)
#This line simply makes a cheeki breeki mask over the entire image so we can highlight things properly.
#Sue me. It's not pretty.
resultsMask = blackGrid.reshape(maxX,maxY)
imageMask = numpy.where(blackGrid,[0,0,0,180],[0,0,0,180]).reshape(maxX,maxY,4)

#We do the edge detection now.

#The grid is shifted up and down one 
wGridDownShift = numpy.roll(whiteGrid.reshape(maxX,maxY),1,0).reshape(maxX * maxY,1)
wGridUpShift = numpy.roll(whiteGrid.reshape(maxX,maxY),-1,0).reshape(maxX * maxY,1)
#Note each pixel has a red and white one next to each other
rwGrid = numpy.where(numpy.logical_or(numpy.logical_and(redGrid,wGridUpShift),numpy.logical_and(redGrid,wGridDownShift)),True,False).reshape(maxX,maxY)

#Get that list of rectangles (we just found each one individually) where the edges blah blah white and red pixels border
rwBorders = scipy.ndimage.measurements.find_objects(scipy.ndimage.measurements.label(scipy.ndimage.morphology.binary_fill_holes(rwGrid))[0])
#This will probably cause more problems than solve them..
#But what it does is try to find sections that are too small to be the stripes we are looking for.
#Yeah already the problems abound right?
rwBorders = [x for x in rwBorders if getWidth(x) >= 3]
#Find the the large rectangles from our red-white rectangles
rwIntermediateGrid,rwIntermediateRect = plotRectangles(rwBorders,maxX,maxY)
#Second pass. Just to make sure. Maybe I shouldn't do this.
rwFinishedGrid,rwBiggerRectangles = plotRectangles(rwIntermediateRect,maxX,maxY)

#TRY TO FIND THE HAIR NOW. THERE IS NO WAY THIS WON'T COMPLICATE THE PROCESS NO SIREEE

#Process is the same as above, but with black now.
blackRect = scipy.ndimage.measurements.find_objects(scipy.ndimage.measurements.label(resultsMask)[0])
hairIntermediateGrid,hairIntermediateRect = plotRectangles(blackRect,maxX,maxY)
hairIntermediateRect = [x for x in hairIntermediateRect if getLength(x) >= 3 and getWidth(x) >= 4]
hairFinalGrid,hairBiggerRectangles = plotRectangles(hairIntermediateRect,maxX,maxY)

#Now that we have the color we now need it to be arranged like Waldo. Or hopefully. HOPEFULLY HE TAKES THE SAME STANCE MAN.
#If there is a sideways waldo, I have no idea what I'll do.

#This for loop goes through our list of rectangles (the red-white ones)
for outsideKey,rectangle in enumerate(rwBiggerRectangles):
	vertical = rectangle[0].stop
	mostRecentHit = vertical
	altVertical = vertical
	possibleStripe = []	
	#Keep looking until you've moved down 8 pixels without hitting a red-white border.
	while altVertical - mostRecentHit < 8:
		altVertical += 1
		possibleStripe.append(outsideKey)
		#Move our counting cursor thing from the left of the rectangle to the right
		for altHorizontal in range(rectangle[1].start,rectangle[1].stop):
			try:
				#Try to read the key plotted at the cursor
				key = rwFinishedGrid[altVertical,altHorizontal]
			except:
				#python throws an error when you so much as look out of bounds
				#JUST RELAX OKAY? I KNOW WHAT I'M DOING I'M NOT WRITING THERE I'M JUST LOOKING
				key = 0
							
			#If the key is not 0 (it's true) then we might have a hit
			if not key == 0:
				possibleStripe.append(key)
				#Reset the "hit"
				mostRecentHit = altVertical

	#There are at least 3 potential stripes here
	if len(set(possibleStripe)) >= 3:
		#It might be Waldo's shirt. PROBABLY NOT THOUGH.
		stripeSection = rectangle
		startHorizontal,startVertical = (stripeSection[1].start,stripeSection[0].start)
		startHorizontal += 3
		altVertical = startVertical
		
		#Go up about thirty or so pixels in a desperate attempt to find any
		#trace of Waldo's hair.
		while (startVertical - altVertical) <= 30 and altVertical >= 1:
			altVertical -= 1
			
			for xSearch in range(startHorizontal - 3,startHorizontal + 3):
				try:	
					if not hairFinalGrid[altVertical,xSearch] == 0:
						#The above statement finds the key. Specifically looking for hair.
						#And no I'm not double checking using that crazy facial recognition thing
						#We looked at in class. Just... No.
						for y in range(startVertical - 35,startVertical + 50):
							for x in range(startHorizontal - 15,startHorizontal + 25):
								try:
									imageMask[y,x] = [255,255,255,0]
								except:
									#If this exception is met then we tried
									#to tamper outside of our border.
									#We don't care.
									pass
						break
				except:
					#Pixel read outside of image. Again, we don't care.
					pass

#All of these next few steps are just layering the dark mask we made a while ago into a 
imagePILMask = Image.fromarray(imageMask.astype('uint8'),"RGBA")
r,g,b,a = imagePILMask.split()
originalImage = scipy.misc.toimage(RGBimg)
originalImage.paste(imagePILMask,mask=a)
originalImage.save(sys.argv[1].split(".")[0]+"-falsePositiveCity.png")
print "SCAN COMPLETE"

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

HDR = ["Page", "Row", "Original name (as read)", "Quantity", "Price (as read)",
       "Predicted name (Begum Bazaar style)", "Strike/correction note", "Ambiguity flag", "Confidence"]

# (row, original, qty, price, predicted, note, flag, confidence)
P1 = [
(1,"12pcs Soup Plate",12,1700,"Soup Plate (12 pcs)","","None","Medium"),
(2,"12pcs Sweet Bowl",12,1100,"Meetha Katori (12 pcs)","","None","Medium"),
(3,"12pcs Sweet Plate",12,1080,"Meetha Plate (12 pcs)","","None","Medium"),
(4,"Tea Spoon",12,280,"Chai Chamcha (12 pcs)","Qty read as 12p [?]","Qty uncertain","Medium"),
(5,"Rice Dish",2,1100,"Chawal Dish (2 pcs)","Qty read as 2p [?]","Qty uncertain","Low"),
(6,"Rice Spoon",2,180,"Chawal Chamcha (2 pcs)","Qty read as 2p [?]","Qty uncertain","Low"),
(7,"Dal Bowl",1,480,"Dal Katori","550 struck through; 480 written beside it","Price correction","Medium"),
(8,"6no ...",2,440,"Name unreadable","Name cut off in photo","Name unreadable","Low"),
(9,"5no ...",1,680,"Name unreadable","Name cut off; price [?]","Name and price unclear","Low"),
(10,"Spoon",1,900,"Chamcha (Spoon)","900 looks high for a spoon","Price suspicious","Low"),
(11,"Tea Glass",12,1100,"Chai Glass (12 pcs)","","None","Medium"),
(12,"Water Glass",12,1300,"Paani Glass (12 pcs)","","None","Medium"),
(13,"Tea Cup",12,180,"Chai Cup (12 pcs)","Price may be per piece","Unit unclear","Low"),
(14,"Soup Box",1,550,"Soup Dabba","","None","Medium"),
(15,"Aikka [?]",1,380,"Unclear (Aikka?)","Name uncertain","Name unclear","Low"),
(16,"Puri Dabba",1,750,"Poori Dabba","Item name struck through","Name struck","Medium"),
(17,"Clip Tiffin Box",1,300,"Clip Tiffin Dabba","","None","Medium"),
(18,"9no Lotha",1,480,"Lota (9 no)","","None","Medium"),
(19,"1no Lotha [?]",1,750,"Lota (1 no)","Price [?]","Price unclear","Low"),
(20,"12no Lotha",2,200,"Lota (12 no)","Qty 2 vs 12 pcs conflict","Qty unclear","Low"),
(21,"Hot Pring [?]",4,2200,"Hot Pot (Pring?)","Name uncertain","Name unclear","Low"),
(22,"Jug [?]",1,790,"Surahi (Jug)","","None","Medium"),
(23,"4KA Priyapoot [?]",1,1100,"Priyapoot (4 ka?)","Name uncertain","Name unclear","Low"),
(24,"Pankutti [?]",2,740,"Pankuti","Price [?]","Price unclear","Low"),
(25,"Chhada Stand [?]",1,480,"Chhada Stand","","Name uncertain","Medium"),
(26,"Soupan [?]",2,760,"Soopan (Soup pan)","","Name uncertain","Medium"),
(27,"Juice Chani [?]",1,480,"Juice Chhanni","","None","Medium"),
(28,"3no Tray",1,550,"Tray (3 no)","","None","Medium"),
(29,"4no Tray",1,750,"Tray (4 no)","Price [?]","Price unclear","Medium"),
(30,"Steel Tray [?]",1,None,"Steel Thali","No price visible","Price missing","Low"),
]
# CHUNK 2 (pages 2-4) will be appended next with append=true, then the workbook builder.
## Basis Data Structure
1.Dictionary:(i,x1,y1,x2,y2):[content]
- key is a tuple for cell location
- value is a list for cell content   
 
2.For each item of the dictionary
- i for sheet index
- x1,y1 for top left cell location
- x2,y2 for bottom right cell location  

## Exceptions
1.[content] could be list of list when:
- cell value itself is a list

- multiple type for one cell:   
..1.text+comment：(1,1,1,1,1):[表格1,Text,负责人,小明，[表格1，Comment,请注意]]  
..2.text+hyperlink

## In Data Flow
Extracted data from excel will be list for later process:
(i,x1,y1,x2,y2,content)





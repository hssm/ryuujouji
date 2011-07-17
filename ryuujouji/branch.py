# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

class Branch:
    
    def __init__(self, parent, segment):

        #If root
        if segment is None:
            self.next_reading = 0
            self.k_in_branch = -1
        else:
            
            #The index in the reading that the next segment in this branch
            #starts at
            self.next_reading = parent.next_reading + len(segment.reading)

            #Increment kanji index if it's a kanji. Also, add to k_in_branch
            #which we use later to calculate the reverse index.
            if segment.is_kanji:
                self.is_kana = False
                self.k_in_branch = parent.k_in_branch + 1
                segment.index = self.k_in_branch
            else:
                self.is_kana = True
                self.k_in_branch = parent.k_in_branch
                segment.index = None
        

        self.parent = parent
        self.segment = segment
         
    def get_branch_as_list(self):
        #Here's a good place to add the reverse kanji index since 
        #we're iterating backwards already.
        indexr = 0
        segments = []
        p = self
        while p.segment is not None:
            if p.segment.is_kanji:
                p.segment.indexr = indexr
                indexr += 1
            else:
                p.segment.indexr = None
            segments.append(p.segment)
            p = p.parent
        segments.reverse()
        return segments


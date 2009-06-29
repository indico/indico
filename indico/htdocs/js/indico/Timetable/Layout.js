
type("TimetableLayoutManager", [],
     {
         _buildCheckpointTable: function(data) {
             /* Checkpoints are time points where events either start or end */
             checkpoints = {};

             var addCheckpoint = function(key, time, type) {
                 if (!checkpoints[time]) {
                     checkpoints[time] = [];
                 }
                 checkpoints[time].push([key, type]);
             };

             each(data, function(value, key){
                 sTime =value.startDate.time.replace(/:/g,'');
                 addCheckpoint(key, sTime, 'start');
                 eTime = value.endDate.time.replace(/:/g,'');

                 if (eTime > sTime) {
                     addCheckpoint(key, eTime, 'end');
                 } else if (eTime == '000000') {
                     addCheckpoint(key, '240000', 'end');
                 }
                 else {
                     addCheckpoint(key, 'nextday', 'end');
                 }
             });

             return checkpoints;
         },

         pointsBetween: function(hStart, hEnd) {
             var result = [];

             each(checkpoints, function(points, time) {
                 if ((hStart == 'nextday' && time == 'nextday') ||
                     (hStart != 'nextday' && time > hStart && time < hEnd))
                 {
                     result = concat(result, points);
                 }
             });

             return result;
         },

         assign: function(assigned, block) {
             var ks = keys(assigned);
             ks.sort();

             for (key in ks) {
                 if (!assigned[key]) {
                     block.assigned = key;
                     assigned[key] = block;
                     return;
                 }
             }

             // nothing assigned in cycle
             // add a new key
             var newElem = ks.length;
             block.assigned = newElem;
             assigned[newElem] = block;
         },

         getBlock: function(blocks, key) {
             var block;
             if (blocks[key]) {
                 block = blocks[key];
             } else {
                 block = blocks[key] = {id: key, collapsed: false};
             }

             return block;
         }
     }
    );


type("IncrementalLayoutManager", ["TimetableLayoutManager"],
     {
         drawDay: function(data) {

             var self = this;

             var checkpoints = this._buildCheckpointTable(data);

             var ks = keys(checkpoints);
             ks.sort();

             var startingHour, endingHour;
             if (ks.length > 1) {
                 startingHour = parseInt(ks[0].substring(0,2), 10);

                 var last = ks.length - 1;

                 // account for 'nextday' entries
                 while(!endingHour){
                     endingHour = parseInt(ks[last].substring(0,2), 10);
                     last--;
                 }

             } else {
                 startingHour = 8;
                 endingHour = 17;
             }

             var endMin;

             var algData = {
                 grid : [],
                 assigned : {},
                 blocks : {},
                 active : 0,
                 currentGroup : [],
                 topPx : 0,
                 groups : []
             };

             var hEnd;

             for (var minutes = 0; minutes < ((endingHour + 1 - startingHour) * 60); minutes += TimetableDefaults.resolution) {

                 // current block is [minutes, minutes + 5]
                 var startMin = (startingHour * 60 + minutes);
                 endMin = (startingHour * 60 + minutes + TimetableDefaults.resolution);
                 var hStart = zeropad(parseInt(startMin/60, 10))+''+zeropad(startMin%60);
                 hEnd = zeropad(parseInt(endMin/60, 10))+''+zeropad(endMin%60);

                 self.processTimeBlock(hStart, hEnd, startMin, minutes, algData);

             }

             if ($L(ks).indexOf('nextday') != null) {
                 self.processTimeBlock('nextday', 'nextday', (startingHour * 60 + minutes), minutes, algData);
             } else {
                 // add last hour + 1 to the grid
                 algData.grid.push([(endMin/60) % 24, algData.topPx]);
             }

             var counter = 0;
             each(algData.groups, function(group) {
                 each(group[0], function(block) {
                     block.group = counter;
                 });
                 counter++;
             });

             return [algData.topPx, algData.grid, algData.blocks, algData.groups];

         }

     });

type("CompactLayoutManager", ["IncrementalLayoutManager"],
     {

         processTimeBlock: function(hStart, hEnd, startMin, minutes, algData) {
             var self = this;

             // get all the checkpoints in [hStart, hEnd]
             var points = self.pointsBetween(hStart, hEnd);
             var incrementPx = 0;

             var block;
             var smallBlockList = [];

             var pxStep = Math.floor(TimetableDefaults.layouts.compact.values.pxPerHour*TimetableDefaults.resolution/60);

             each(points, function(point) {
                 if (point[1] == 'end') {
                     block = self.getBlock(algData.blocks, point[0]);

                     block.end = algData.topPx;

                     if (algData.assigned[block.assigned]) {
                         algData.active--;
                         // this means it has been started in a previous timeslot
                         algData.assigned[block.assigned] = null;

                         // diff: how much does it take for the block to reach
                         // the minimum size?
                         var diff = TimetableDefaults.layouts.compact.values.minPxPerBlock - (block.end - block.start);

                         if (diff > 0){
                             // increase it by diff
                             block.end += diff;
                             incrementPx = diff>incrementPx?diff:incrementPx;
                             algData.topPx += incrementPx;
                         }
                         // check if block goes beyond the timetable limits
                         // (ends after midnight)
                         if (hStart == 'nextday') {
                             // mark it as 'unfinished' and add an extra space
                             block.end += hStart=='nextday'?20:0;
                             block.unfinished = true;
                         }

                     } else {
                         // otherwise, it is ending just before it starts:
                         // this means that the duration is less than our "resolution"
                         // so, let's add it to smallBlockList
                         smallBlockList.push(block);
                     }
                 }
             });

             if (minutes % 60 === 0) {
                 algData.grid.push([startMin/60%24, algData.topPx]);
             }

             if (!algData.active) {
                 if (algData.currentGroup.length > 0) {
                     algData.groups.push([algData.currentGroup, keys(algData.assigned).length]);
                     algData.currentGroup = [];
                     algData.assigned = {};
                 }
             }

             each(points, function(point) {
                 if (point[1] == 'start') {
                     block = self.getBlock(algData.blocks, point[0]);

                     block.start = algData.topPx;
                     algData.active++;
                     self.assign(algData.assigned, block);
                     algData.currentGroup.push(block);
                 }
             });

             if (algData.active > 0) {
                 algData.topPx += pxStep;
             } else {
                 algData.topPx += TimetableDefaults.layouts.compact.values.pxPerSpace;
             }

             each(smallBlockList, function(block) {
                 block.end = block.start + TimetableDefaults.layouts.compact.values.minPxPerBlock;
                 algData.topPx += TimetableDefaults.layouts.compact.values.minPxPerBlock;
                 algData.assigned[block.assigned] = null;
                 algData.active--;
             });
         }
     });

type("ProportionalLayoutManager", ["IncrementalLayoutManager"],
     {

         processTimeBlock: function(hStart, hEnd, startMin, minutes, algData) {
             var self = this;

             // get all the checkpoints in [hStart, hEnd]
             var points = self.pointsBetween(hStart, hEnd);
             var incrementPx = 0;

             var block;

             var pxStep = Math.floor(TimetableDefaults.layouts.proportional.values.pxPerHour*TimetableDefaults.resolution/60);
             var smallBlocks = [];


             each(points, function(point) {

                 if (point[1] == 'end') {
                     block = self.getBlock(algData.blocks, point[0]);

                     block.end = algData.topPx;

                     if (algData.assigned[block.assigned]) {
                         algData.active--;
                         algData.assigned[block.assigned] = null;

                         var diff = TimetableDefaults.layouts.proportional.values.minPxPerBlock - (block.end - block.start);
                         if (diff > 0) {
                             block.end += diff;
                             block.collapsed = true;
                             algData.topPx += diff;
                         }

                         // check if block goes beyond the timetable limits
                         // (ends after midnight)
                         if (hStart == 'nextday') {
                             // mark it as 'unfinished' and add an extra space
                             block.end += hStart=='nextday'?20:0;
                             block.unfinished = true;
                         }

                     } else {
                         smallBlocks.push(block);
                     }

                 }
             });

             if (minutes % 60 === 0) {
                 algData.grid.push([startMin/60%24, algData.topPx]);
             }

             if (!algData.active) {
                 if (algData.currentGroup.length > 0) {
                     algData.groups.push([algData.currentGroup, keys(algData.assigned).length]);
                     algData.currentGroup = [];
                     algData.assigned = {};
                 }
             }

             each(points, function(point) {
                 if (point[1] == 'start') {
                     block = self.getBlock(algData.blocks, point[0]);

                     block.start = algData.topPx;
                     algData.active++;
                     self.assign(algData.assigned, block);
                     algData.currentGroup.push(block);
                 }
             });

             each(smallBlocks, function(block) {
                 algData.active--;
                 algData.assigned[block.assigned] = null;
                 block.collapsed = true;
                 block.end = algData.topPx + TimetableDefaults.layouts.proportional.values.minPxPerBlock;
             });

             if (smallBlocks.length > 0) {
                 algData.topPx += TimetableDefaults.layouts.proportional.values.minPxPerBlock;
             }

             algData.topPx += pxStep;
         }
     });

type("TimetableLayoutMenu", ["PopupMenu"],
     {
     },
     function(triggerElement, timetableDrawer) {
         this.PopupMenu({
             'White space': new RadioPopupWidget({"compact": $T('Compact'),
                                                  "proportional": $T('Proportional')},
                                                 timetableDrawer.layout,
                                                 [triggerElement, this]),
             'Detail': new RadioPopupWidget({"session": $T('Session'),
                                             "contribution": $T('Contribution')},
                                            timetableDrawer.detail,
                                            [triggerElement, this])
         }, [triggerElement]);
         this.timetableDrawer = timetableDrawer;
     });

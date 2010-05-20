
type("TimetableLayoutManager", [],
     {
         _buildCheckpointTable: function(data) {
             /* Checkpoints are time points where events either start or end */
             checkpoints = {};
             var addCheckpoint = function(key, time, type, sessionId) {

                 if (!checkpoints[time]) {
                     checkpoints[time] = [];
                 }
                 checkpoints[time].push([key, type, sessionId]);
             };

             each(data, function(value, key){
                 sTime =value.startDate.time.replace(/:/g,'');
                 eTime = value.endDate.time.replace(/:/g,'');

                 // If a poster session with a duration of > 7h then don't place
                 // it in the grid but rather on the top as a whole day event
                 if (value.isPoster && value.duration > (TimetableDefaults.wholeDay*60)) {
                     addCheckpoint(key, sTime, 'wholeday', value.sessionId);
                 }
                 else {
                     addCheckpoint(key, sTime, 'start', value.sessionId);

                 if (eTime > sTime) {
                     addCheckpoint(key, eTime, 'end');
                 } else if (eTime == '000000') {
                     addCheckpoint(key, '240000', 'end');
                 }
                 else {
                     addCheckpoint(key, 'nextday', 'end');
                 }
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

         reorderAssigned: function(assigned, lastAssigned, currentGroup) {

             var correctlyAssigned = function(block) {
                 return exists(lastAssigned[block.sessionId]) && lastAssigned[block.sessionId].col == block.assigned;
             };

             // Returns number of previously processed session slots
             var numAssignedBlocks = function(sessionId) {
                 var blocks = lastAssigned[sessionId].blocks;
                 var keyss = keys(blocks);
                 var length = keyss.length;
                 return length;
             };

             // Adds/updates a block in the lastAssigned dictionary
             var lastAssign = function(block, col) {

                 if (!exists(lastAssigned[block.sessionId])) {
                     lastAssigned[block.sessionId] = {'blocks': {}};
                 }
                 if (col !== undefined) {
                     lastAssigned[block.sessionId].col = col;
                 }
                 lastAssigned[block.sessionId].blocks[block.id] = true;
             };

             // Changes the column of a block
             var reassign = function(block, col) {
                 block.assigned = col;
                 assigned[col] = block;
                 if (!exists(block.sessionId)) {
                     lastAssign(block, col);
                 }
             };

             for (key in currentGroup) {
                 var block = currentGroup[key];

                 // If this is not a session slot (that is a block
                 // that has sessionId set) then we don't care about in
                 // which column it is placed
                 if (!exists(block.sessionId)) {
                     continue;
                 }

                 if (!exists(lastAssigned[block.sessionId])) {
                     // This block has never been assigned before. Just update the lastAssigned.
                     lastAssign(block, block.assigned);
                     continue;
                 }

                 lastAssign(block);

                 if (correctlyAssigned(block)) {
                     // The block has already got its prefered position
                     continue;
                 }

                 var preferedCol = lastAssigned[block.sessionId].col;
                 var existingBlock = assigned[preferedCol];

                 // If there's no block on the prefered column it means
                 // that there are fewer columns this time.
                 if (!existingBlock) {
                     // Forcing to use prefered column is not very nice
                     // for now do nothing
                     /*
                     for (var i = preferedCol-1; i >= 0; i--) {
                         if (!assigned[preferedCol]) {
                             existingBlock = assigned[i];
                             preferedCol = i;
                             break;
                         }
                     }
                     reassign(block, preferedCol);
                     */
                     continue;
                 }

                 // Try to place the block in the prefered column
                 if (!exists(existingBlock.sessionId) || !exists(lastAssigned[existingBlock.sessionId]) ||
                     numAssignedBlocks(block.sessionId) > numAssignedBlocks(existingBlock.sessionId)) {

                     // The block currently placed in the prefered column has either no prefered column
                     // or has a preferred column but has fewer previous placed session slots (this
                     // gives lower priority).

                     // Only do the swap if the existing block starts at the same time
                     // otherwise there might be overlapping blocks. Is there a better way
                     // to handle this so that this check is not needed?
                     if (existingBlock.start == block.start) {
                         reassign(existingBlock, block.assigned);
                         reassign(block, preferedCol);
                     }
                 }
             }

         },

         getBlock: function(blocks, key) {
             var block;
             if (blocks[key]) {
                 block = blocks[key];
             } else {
                 block = blocks[key] = {id: key, collapsed: false};
             }

             return block;
         },

         addWholeDayBlock: function(blocks, key) {
             block = blocks[key] = {id: key};
         }
     }
    );


type("IncrementalLayoutManager", ["TimetableLayoutManager"],
     {
         drawDay: function(data, detailLevel, startTime, endTime) {

             var self = this;

             this.detailLevel = any(detailLevel, 'session');

             var checkpoints = this._buildCheckpointTable(data);

             var ks = keys(checkpoints);
             ks.sort();

             var startingHour, endingHour;
             if (ks.length > 1) {
                 startingHour = parseInt(ks[0].substring(0,2), 10);

                 var last = ks.length - 1;

                 // account for 'nextday' entries
                 while(!endingHour && last >= 0){
                     endingHour = parseInt(ks[last].substring(0,2), 10);
                     last--;
                 }

             } else {
                 startingHour = parseInt(any(startTime, '8:00').split(':')[0], 10);
                 endingHour = parseInt(any(endTime, '17:00').split(':')[0],10);
             }

             var endMin;

             var algData = {
                 grid : [],             // Positions of all the time lines
                 assigned : {},         // colums bound to blocks
                 blocks : {},           // Dict of blocks
                 active : 0,            // number of of active time blocks
                 currentGroup : [],     // current processed group
                 topPx : 0,             // counter when iterating from top to bottom of timetable
                 groups : [],           // Isolated group of timetable blocks (all blocks in parallel)
                 extraPx : {},          // Used for increasing the pixels for time blocks. Used when a time
                                        // time table block needs extra space.
                 lastAssigned : {},      // Remembers to what column a session has been assigned before
                                        // makes it possible align sessions under each other
                 wholeDayBlocks : {}    // All the block that should be shown as spanning the whole day,
                                        // i.e. a poster session.
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

             if ($L(ks).indexOf('nextday') !== null) {
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

             return [algData.topPx, algData.grid, algData.blocks, algData.groups, algData.wholeDayBlocks];

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

             var blockAdded = false;

             each(points, function(point) {
                 if (point[1] == 'start') {
                     blockAdded = true;

                     block = self.getBlock(algData.blocks, point[0]);
                     block.sessionId = point[2];

                     block.start = algData.topPx;
                     algData.active++;
                     self.assign(algData.assigned, block);
                     algData.currentGroup.push(block);
                 } else if (point[1] == 'wholeday') {
                     self.addWholeDayBlock(algData.wholeDayBlocks, point[0]);
                 }
             });

             // Try to reaorder the assigned blocks based on their previous position
             if (blockAdded) {
                 self.reorderAssigned(algData.assigned, algData.lastAssigned, algData.currentGroup);
             }

             if (algData.active > 0) {
                 var extraPx = 0;
                 each(algData.extraPx, function(value, key) {
                     if (value > extraPx) {
                         extraPx = value;
                     }
                 });
                 algData.topPx += pxStep + extraPx;
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


type("PosterLayoutManager", ["TimetableLayoutManager"],
    {
        drawDay: function(data, detailLevel) {
            return data;
        }
    });


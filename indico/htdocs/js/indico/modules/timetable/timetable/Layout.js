/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */


type("TimetableLayoutManager", [],
     {
         _buildCheckpointTable: function(data) {
             /* Checkpoints are time points where events either start or end */
             var checkpoints = {};
             var addCheckpoint = function(key, time, type, sessionId, sessionSlotId) {

                 if (!checkpoints[time]) {
                     checkpoints[time] = [];
                 }
                 checkpoints[time].push([key, type, sessionId, sessionSlotId]);
             };


             // Enforce key ordering
             // In case we are dealing with structures that are inside a session,
             // and have a non-null sessionCode, use it for ordering
             var orderedKeys = keys(data);

             orderedKeys.sort(function(e1, e2) {
                 // if there's a session code
                 if (exists(data[e1].sessionCode) &&
                     exists(data[e2].sessionCode)) {
                     var byCode = SortCriteria.Integer(data[e1].sessionCode,
                                                       data[e2].sessionCode);
                     if (byCode != 0) {
                         return byCode;
                     }
                 }

                 // default behavior
                 return SortCriteria.Integer(e1, e2);
             });

             each(orderedKeys, function(key){
                 var value = data[key];
                 var sTime = value.startDate.time.replace(/:/g,'');
                 var eTime = value.endDate.time.replace(/:/g,'');

                 // If a poster session with a duration of > 7h then don't place
                 // it in the grid but rather on the top as a whole day event
                 if (value.isPoster && value.duration > (TimetableDefaults.wholeDay*60)) {
                     addCheckpoint(key, sTime, 'wholeday', value.sessionId, value.sessionSlotId);
                 }
                 else {
                     addCheckpoint(key, sTime, 'start', value.sessionId, value.sessionSlotId);

                     if (eTime >= sTime) {
                         addCheckpoint(key, eTime, 'end');
                     } else if (eTime == '000000') {
                         addCheckpoint(key, '240000', 'end');
                     }
                     else {
                         addCheckpoint(key, 'nextday', 'end');
                     }
                 }
             });
             this.checkpoints = checkpoints;
             return checkpoints;
         },

         pointsBetween: function(hStart, hEnd) {
             var result = [];

             each(this.checkpoints, function(points, time) {
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

             for (var key in ks) {
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

         reorderAssigned: function(assigned, lastAssigned, currentGroup, currentPos) {

             var getLastAssignedId = function(block) {
                return "{0}l{1}".format(block.sessionId, block.sessionSlotId);
             };

             var correctlyAssigned = function(block) {
                 return exists(lastAssigned[getLastAssignedId(block)]) && lastAssigned[getLastAssignedId(block)].col == block.assigned;
             };

             // Returns number of previously processed session slots
             var numAssignedBlocks = function(sessionId) {
                 return keys(lastAssigned[sessionId].blocks).length;
             };

             // Adds/updates a block in the lastAssigned dictionary
             var lastAssign = function(block, col) {

                 if (!exists(lastAssigned[getLastAssignedId(block)])) {
                     lastAssigned[getLastAssignedId(block)] = {'blocks': {}};
                 }
                 if (col !== undefined) {
                     lastAssigned[getLastAssignedId(block)].col = col;
                 }
                 lastAssigned[getLastAssignedId(block)].blocks[block.id] = true;
             };

             // Changes the column of a block
             var reassign = function(block, col) {
                 assigned[block.assigned] = null;
                 block.assigned = col;
                 assigned[col] = block;
                 lastAssign(block, col);
             };

             var swap_columns = function(block1, block2) {
                 var block1_old_col = block1.assigned;
                 reassign(block1, block2.assigned);
                 reassign(block2, block1_old_col);
                 assigned[block1.assigned] = block1;
             };

             for (var key in currentGroup) {
                 var block = currentGroup[key];

                 // If this is not a session slot (that is a block
                 // that has sessionId set) then we don't care about in
                 // which column it is placed
                 if (!exists(block.sessionId)) {
                     continue;
                 }

                 if (exists(lastAssigned[getLastAssignedId(block)])) {
                     lastAssign(block);
                 } else {
                     // This block has never been assigned before. Just update the lastAssigned.
                     lastAssign(block, block.assigned);
                     continue;
                 }

                 if (correctlyAssigned(block)) {
                     // The block has already got its prefered position
                     continue;
                 }

                 var preferedCol = lastAssigned[getLastAssignedId(block)].col;
                 var existingBlock = assigned[preferedCol];

                 // If there's no block on the prefered column
                 if (!existingBlock) {
                     // if the block starts at the current position, it is safe to move it to a free place
                     // otherwise we can overlap an exisiting one
                     if (block.start == currentPos && preferedCol < _(assigned).size()) {
                         reassign(block, preferedCol);
                     }
                 } else if (!exists(existingBlock.sessionId) || !exists(lastAssigned[existingBlock.sessionId]) ||
                     numAssignedBlocks(block.sessionId) > numAssignedBlocks(existingBlock.sessionId)) {
                     // The block currently placed in the prefered column has either no prefered column
                     // or has a preferred column but has fewer previous placed session slots (this
                     // gives lower priority).

                     // Only do the swap if the existing block starts at the same time
                     // otherwise there might be overlapping blocks. Is there a better way
                     // to handle this so that this check is not needed?
                     if (existingBlock.start == block.start) {
                         swap_columns(existingBlock, block)
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
             blocks[key] = {id: key};
         },

         getNumColumnsForGroup: function(group) {
             return group[1];
         },

         getHeader: function() {
             return null;
         },

         shouldShowRoom: function() {
             return true;
         },
         reorderColumns:function(group) {
         }
     }
    );


type("IncrementalLayoutManager", ["TimetableLayoutManager"],
     {
         name: 'incremental',
         drawDay: function(data, detailLevel, startTime, endTime, managementMode) {
             var self = this;

             this.eventData = data;

             this.detailLevel = any(detailLevel, 'session');

             var checkpoints = this._buildCheckpointTable(data);

             var ks = keys(checkpoints);
             ks.sort();
             managementMode = any(managementMode, true);
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

             if(managementMode){
             //add hour before start if we are in management mode
                 if (startingHour > 0) {
                     for (var min = 0; min < 60 ; min += TimetableDefaults.resolution) {
                         self.processTimeBlock(startingHour - 1, startingHour, (startingHour - 1) * 60, min, algData);
                     }
                 }
             }

             for (var minutes = 0; minutes < ((endingHour + 1 - startingHour) * 60); minutes += TimetableDefaults.resolution) {
                 // current block is [minutes, minutes + 5]
                 var startMin = (startingHour * 60 + minutes);
                 endMin = (startingHour * 60 + minutes + TimetableDefaults.resolution);
                 var hStart = zeropad(parseInt(startMin / 60, 10)) + '' + zeropad(startMin % 60);
                 hEnd = zeropad(parseInt(endMin / 60, 10)) + '' + zeropad(endMin % 60);

                 self.processTimeBlock(hStart, hEnd, startMin, minutes, algData);
             }

             if ($L(ks).indexOf('nextday') !== null) {
                 self.processTimeBlock('nextday', 'nextday', (startingHour * 60 + minutes), minutes, algData);
             } else if (endMin/60 < 25 && managementMode){
                 // add last hour + 1 to the grid
                 // (only if the next hour is not after midnight)
                 algData.grid.push([(endMin/60) % 24, algData.topPx]);
             }

             var counter = 0;
             each(algData.groups, function(group) {
                 self.reorderColumns(group[0]);
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

         name: 'compact',
         processTimeBlock: function(hStart, hEnd, startMin, minutes, algData) {
             var self = this;

             // get all the checkpoints in [hStart, hEnd]
             var points = self.pointsBetween(hStart, hEnd);
             var incrementPx = 0;

             var block;
             var smallBlockList = [];

             var pxStep = Math.floor(TimetableDefaults.layouts.compact.values.pxPerHour*TimetableDefaults.resolution/60);

             var endPoints = [];

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

                         // save reference for all blocks that end here, will use it below
                         endPoints.push(block);

                     } else {
                         // otherwise, it is ending just before it starts:
                         // this means that the duration is less than our "resolution"
                         // so, let's add it to smallBlockList
                         smallBlockList.push(block);
                     }
                 }
             });

             if (endPoints.length) {
                 // now every block that ends at this point must have the same 'end"
                 // since some of them may have been expanded ('diff' above), we need to set them all
                 // to the max value
                 var maxPx = _(endPoints).max(function(block){ return block.end; }).end;
                 _(endPoints).each(function(block) {
                     block.end = maxPx;
                 });
             }

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
                     block.sessionSlotId = point[3];

                     block.start = algData.topPx;
                     algData.active++;
                     self.assign(algData.assigned, block);
                     algData.currentGroup.push(block);
                 } else if (point[1] == 'wholeday') {
                     self.addWholeDayBlock(algData.wholeDayBlocks, point[0]);
                 }
             });

             // Try to reaorder the assigned blocks based on their session siblings' position
             if (blockAdded) {
                 self.reorderAssigned(algData.assigned, algData.lastAssigned, algData.currentGroup, algData.topPx);
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
         name: 'proportional',
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

             var hour = startMin / 60;
             if (minutes % 60 === 0 && hour <= 24) {
                 algData.grid.push([hour % 24, algData.topPx]);
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

type("RoomLayoutManager", ["CompactLayoutManager"],
    {

        drawDay: function(data, detailLevel, startTime, endTime) {
            this.roomsCols = {};
            return this.CompactLayoutManager.prototype.drawDay.call(this, data, detailLevel, startTime, endTime);
        },

        assign: function(assigned, block) {
            var roomName = this.eventData[block.id].room;
            var col = 0;
            if (! exists(this.roomsCols[roomName])) {
                // If there is no room name, the block will be in the column 0 (and take all the available width)
                if (trim(roomName) !== "") {
                    col = this.roomsCols[roomName] = keys(this.roomsCols).length;
                }
            } else {
                col = this.roomsCols[roomName];
            }

            block.assigned = col;
            assigned[col] = block;
        },

        reorderColumns: function(currentGroup) {
            var self = this;
            var roomNames = keys(this.roomsCols);
            roomNames.sort();

            this.roomsCols = {};
            var counter = 0;
            each (roomNames, function(name) {
                self.roomsCols[name] = counter;
                counter++;
            });

            for (var key in currentGroup) {
                var block = currentGroup[key];
                var roomName = this.eventData[block.id].room;
             // If there is no room name, the block will be in the column 0 (and take all the available width)
                var col = 0;
                if (trim(roomName) !== "") {
                    col =  this.roomsCols[roomName];
                }
                block.assigned = col;
            }

        },

        getNumColumnsForGroup: function(group) {
            if (group[0].length == 1 && this.eventData[group[0][0].id].room === "") {
                return 1;
            } else {
                return keys(this.roomsCols).length;
            }
        },

        getHeader: function(width) {
            var roomNames = keys(this.roomsCols);
            var cols = roomNames.length;
            var borderPixels = 1; // this is because of the separators between the room names
            return Html.div({style:{marginLeft:pixels(TimetableDefaults.leftMargin), paddingBottom:pixels(10), paddingTop:pixels(20)}},
                    translate(roomNames, function(key){
                        return Html.div({className: "headerRoomLayoutTimeTable",
                                         style:{width:pixels(Math.floor((width-TimetableDefaults.leftMargin)/cols)-borderPixels)}
                                        }, key);
                    })
                    );
        },

        shouldShowRoom: function() {
            return false;
        }
    },

    function() {
        this.roomsCols = {};
    });


type("PosterLayoutManager", ["TimetableLayoutManager"],
    {
        drawDay: function(data, detailLevel) {
            return data;
        }
    });

  # -*- coding: latin-1 -*-
import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *


##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "ProblemChild")
        #the coordinates of the agent's food and tunnel will be stored in these
        #variables (see getMove() below)
        self.myFood = None
        self.myTunnel = None
    
    ##
    #getPlacement 
    #
    # The agent uses a hardcoded arrangement for phase 1 to provide maximum
    # protection to the queen.  Enemy food is placed randomly.
    #
    def getPlacement(self, currentState):
        self.myFood = None
        self.myTunnel = None
        if currentState.phase == SETUP_PHASE_1:
            return [(0,0), (5, 1), 
                    (9,3), (1,2), (2,1), (3,0), \
                    (9,2), (1,1), (2,0), \
                    (9,1), (1,0) ];
        elif currentState.phase == SETUP_PHASE_2:
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:            
            return None  #should never happen
    
    ##
    #getMove
    #
    # This agent gathers food, defends the queen, and attacks the enemy
    # queen.  The queen is never moved.
    #
    ##
    def getMove(self, currentState):
        #asciiPrintState(currentState)
        #Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        #the first time this method is called, the food and tunnel locations
        #need to be recorded in their respective instance variables
        if (self.myTunnel == None):
            self.myTunnel = getConstrList(currentState, me, (TUNNEL,))[0]
        if (self.myFood == None):
            foods = getConstrList(currentState, None, (FOOD,))
            self.myFood = foods[0]
            #find the food closest to the tunnel
            bestDistSoFar = 1000 #i.e., infinity
            for food in foods:
                dist = stepsToReach(currentState, self.myTunnel.coords, food.coords)
                if (dist < bestDistSoFar):
                    self.myFood = food
                    bestDistSoFar = dist

        #if I don't have a worker, give up.  QQ
        numAnts = len(myInv.ants)
        if (numAnts == 1):
            return Move(END, None, None)

        #if the worker has already moved, we're done
        workerList = getAntList(currentState, me, (WORKER,))
        if (len(workerList) < 1):
            return Move(END, None, None)
        else:
            myWorker = workerList[0]
            if (myWorker.hasMoved):
                return Move(END, None, None)


        #if the queen is on the anthill move her
        myQueen = myInv.getQueen()
        if (myQueen.coords == myInv.getAnthill().coords):
            return Move(MOVE_ANT, [myInv.getQueen().coords, (1,0)], None)

        # if a soldier is on the anthill move it
        mySoldiers = getAntList(currentState, me, (SOLDIER,))
        for soldier in mySoldiers:
            if (not soldier.hasMoved):
                if (soldier.coords == myInv.getAnthill().coords):
                    return Move(MOVE_ANT, [soldier.coords, (0,1)], None)

        myWorkers = getAntList(currentState, me, (WORKER,))
        for worker in myWorkers:
            if (not worker.hasMoved):
                if (worker.coords == myInv.getAnthill().coords):
                    return Move(MOVE_ANT, [worker.coords, (1,0)], None)

        # if the hasn't moved, have her move to the side
        if (not myQueen.hasMoved):
            if (myQueen.coords != (0, 3)):
                path = createPathToward(currentState, myQueen.coords,
                                        (0, 3), UNIT_STATS[QUEEN][MOVEMENT])
                return Move(MOVE_ANT, path, None)
            else:
                return Move(MOVE_ANT, [myQueen.coords], None)



        #if I have a bit of food, only a few ants and the anthill is unoccupied then
        #make a worker
        if (myInv.foodCount > 2 and len(myInv.ants) < 3):
            if (getAntAt(currentState, myInv.getAnthill().coords) is None):
                return Move(BUILD, [myInv.getAnthill().coords], DRONE)

        if (myInv.foodCount > 2 and len(myInv.ants) < 4):
            if (getAntAt(currentState, myInv.getAnthill().coords) is None):
                return Move(BUILD, [myInv.getAnthill().coords], DRONE)

        # if I have more food and the anthill is unoccupied then
        # make a soldier
        if (myInv.foodCount >= 3 and numAnts <= 8):
            if (getAntAt(currentState, myInv.getAnthill().coords) is None):
                return Move(BUILD, [myInv.getAnthill().coords], SOLDIER)


        #Move all my soldiers towards the queen
        enemyInv = getEnemyInv(self, currentState)
        enemyQueen = enemyInv.getQueen()
        enemyAnthill = enemyInv.getAnthill()
        i = 0
        mySoldiers = getAntList(currentState, me, (SOLDIER,))
        for soldier in mySoldiers:
            if not (soldier.hasMoved):
                if i % 2 == 0:
                    path = createPathToward(currentState, soldier.coords,
                                            enemyQueen.coords, UNIT_STATS[SOLDIER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)
                elif i % 2 == 1:
                    path = createPathToward(currentState, soldier.coords,
                                        (9, 0), UNIT_STATS[SOLDIER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)
            i += 1

        for checkAnt in enemyInv.ants:
            if checkAnt.type == WORKER:
                target = checkAnt
            else:
                target = enemyInv.getQueen()

        myDrones = getAntList(currentState, me, (DRONE,))
        for drone in myDrones:
            if not (drone.hasMoved):
                path = createPathToward(currentState, drone.coords,
                                        target.coords, UNIT_STATS[DRONE][MOVEMENT])
                return Move(MOVE_ANT, path, None)


        #apply the following to all workers
        myWorkers = getAntList(currentState, me, (WORKER,))
        for worker in myWorkers:
            # if the worker has food, move toward tunnel
            if (worker.carrying):
                path = createPathToward(currentState, worker.coords,
                                    self.myTunnel.coords, UNIT_STATS[WORKER][MOVEMENT])
                return Move(MOVE_ANT, path, None)
            
            #if the worker has no food, move toward food
            else:
                path = createPathToward(currentState, worker.coords,
                                    self.myFood.coords, UNIT_STATS[WORKER][MOVEMENT])
                return Move(MOVE_ANT, path, None)
        return Move(END, None, None)

    ##
    #getAttack
    #
    # This agent never attacks
    #
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        return enemyLocations[0]  #don't care
        
    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

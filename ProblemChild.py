# -*- coding: latin-1 -*-
import random
import sys

sys.path.append("..")  # so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *

g_food_coordinates = []
g_construct_coords_except_grass = []
optimal_food_coords = []
worker_information = {}
should_entropy_be_added_to_workers = 0


##
# AIPlayer
# Description: The responsbility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# will be implemented by students in Dr. Nuxoll's AI course.
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "ProblemChild")
        # the coordinates of the agent's food and tunnel will be stored in these
        # variables (see getMove() below)
        self.myFood = None
        self.myTunnel = None

    ##
    # getPlacement
    #
    # The agent uses a hardcoded arrangement for phase 1 to provide maximum
    # protection to the queen.  Enemy food is placed randomly.
    #
    def getPlacement(self, currentState):
        self.myFood = None
        self.myTunnel = None
        if currentState.phase == SETUP_PHASE_1:
            return [(0, 0), (5, 2), (0, 3), (1, 2), (2, 1), (3, 0), (0, 2), (1, 1), (2, 0), (0, 1), (1, 0)]

        elif currentState.phase == SETUP_PHASE_2:

            enemy = 1 - currentState.whoseTurn
            enemy_hill = getConstrList(currentState, enemy, (ANTHILL,))[0]
            enemy_tunnel = getConstrList(currentState, enemy, (TUNNEL,))[0]

            numToPlace = 2
            moves = []

            furthest_from_hill_coords = [(0, 0), (0, 0)]
            furthest_from_tunnel_coords = [(0, 0), (0, 0)]
            hill_furthest_1 = 0
            hill_furthest_2 = 0
            tunn_furthest_1 = 0
            tunn_furthest_2 = 0

            for yPos in range(6, 10):
                for xPos in range(0, 10):
                    # Skip if there is an existing construct
                    if getConstrAt(currentState, (xPos, yPos)):
                        continue

                    # Finding the two pairs of coordinates, 2 positions that are furthest from the hill, and two that are furthest from the tunnel
                    current_hill_distance = stepsToReach(currentState, (xPos, yPos), enemy_hill.coords)
                    current_tunnel_distance = stepsToReach(currentState, (xPos, yPos), enemy_tunnel.coords)

                    if (current_hill_distance > hill_furthest_1) and (xPos, yPos) not in furthest_from_tunnel_coords:
                        hill_furthest_1 = current_hill_distance

                        furthest_from_hill_coords[0] = (xPos, yPos)

                    elif (current_hill_distance > hill_furthest_2) and (
                    xPos, yPos) not in furthest_from_hill_coords and (xPos, yPos) not in furthest_from_tunnel_coords:
                        hill_furthest_2 = current_hill_distance
                        furthest_from_hill_coords[1] = (xPos, yPos)

                    if (current_tunnel_distance > tunn_furthest_1) and (xPos, yPos) not in furthest_from_hill_coords:
                        tunn_furthest_1 = current_tunnel_distance
                        furthest_from_tunnel_coords[0] = (xPos, yPos)

                    elif (current_tunnel_distance > tunn_furthest_2) and (
                    xPos, yPos) not in furthest_from_tunnel_coords and (xPos, yPos) not in furthest_from_hill_coords:
                        tunn_furthest_2 = current_tunnel_distance
                        furthest_from_tunnel_coords[1] = (xPos, yPos)

            # Taking the average of the max distance coordinates to find the best possible food placement
            furthest_coords_list = furthest_from_hill_coords + furthest_from_tunnel_coords
            furthest_coord_avg = []
            for coords in furthest_coords_list:
                avg_distance = furthest_coord_avg.append((stepsToReach(currentState, coords,
                                                                       enemy_hill.coords) + stepsToReach(currentState,
                                                                                                         coords,
                                                                                                         enemy_tunnel.coords)) / 2)

            index = furthest_coord_avg.index(max(furthest_coord_avg))
            moves.append(furthest_coords_list[index])
            furthest_coords_list[index], furthest_coord_avg[index] = 0, 0
            moves.append(furthest_coords_list[furthest_coord_avg.index(max(furthest_coord_avg))])

            me = currentState.whoseTurn
            g_construct_coords_except_grass.append(getConstrList(currentState, me, (ANTHILL,))[0].coords)
            g_construct_coords_except_grass.append(getConstrList(currentState, me, (TUNNEL,))[0].coords)

            return moves
        else:
            return NONE  # This should never happen

    ##
    # getMove
    #
    # This agent simply gathers food as fast as it can with its worker.  It
    # never attacks and never builds more ants.  The queen is never moved.
    #
    ##
    def getMove(self, currentState):
        # Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn
        enemy = 1 - me
        # the first time this method is called, the food and tunnel locations
        # need to be recorded in their respective instance variables
        if (self.myTunnel == None):
            self.myTunnel = getConstrList(currentState, me, (TUNNEL,))[0]
        if (self.myFood == None):
            foods = getConstrList(currentState, None, (FOOD,))
            self.myFood = foods[0]
            # find the food closest to the tunnel
            bestDistSoFar = 1000  # i.e., infinity
            for food in foods:
                dist = stepsToReach(currentState, self.myTunnel.coords, food.coords)
                if food.coords[1] <= 4:
                    g_food_coordinates.append(food.coords)
                    g_construct_coords_except_grass.append(food.coords)
                if (dist < bestDistSoFar):
                    self.myFood = food
                    bestDistSoFar = dist

        hill_location = g_construct_coords_except_grass[0]
        tunn_location = g_construct_coords_except_grass[1]

        # Moving the queen off of the ant hill to a valid position
        myQueen = myInv.getQueen()
        if (myQueen.coords == hill_location):
            queen_x = myQueen.coords[0]
            queen_y = myQueen.coords[1]

            polarity = [(0, 1), (0, -1), (-1, 0), (-1, -1)]
            for p in polarity:
                if (queen_x + p[0]) > 9 or (queen_x + p[0]) < 0 or (queen_y + p[1]) > 3 or (queen_y + p[1]) < 0:
                    continue

                return Move(MOVE_ANT, [myInv.getQueen().coords, (queen_x + p[0], queen_y + p[1])], None)

        # if the queen hasn't moved, have her move in place so she will attack
        if (not myQueen.hasMoved):
            return Move(MOVE_ANT, [myQueen.coords], None)
        # if I don't have a worker, give up.  QQ
        numAnts = len(myInv.ants)
        if (numAnts == 1):
            return Move(END, None, None)

        min_worker_num = 2
        myWorker = getAntList(currentState, me, (WORKER,))

        food_count = myInv.foodCount

        if (food_count >= 1) and (len(myWorker) < min_worker_num):
            return Move(BUILD, [hill_location], WORKER)

        for worker in myWorker:
            if not worker.hasMoved:

                # Move worker off of anthill to find food
                mvAnt = clearWorkerFromConstructs(currentState, hill_location, worker.coords, self.myFood.coords)
                if (mvAnt):
                    path = createPathToward(currentState, worker.coords, mvAnt, UNIT_STATS[WORKER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)

                # Move worker off of tunnel to find food
                mvAnt = clearWorkerFromConstructs(currentState, tunn_location, worker.coords, self.myFood.coords)
                if (mvAnt):
                    path = createPathToward(currentState, worker.coords, mvAnt, UNIT_STATS[WORKER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)

                    # if the worker has food, move toward tunnel
                if (worker.carrying):
                    path = createPathToward(currentState, worker.coords, self.myTunnel.coords,
                                            UNIT_STATS[WORKER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)


                # if the worker has no food, move toward food
                else:
                    path = createPathToward(currentState, worker.coords, self.myFood.coords,
                                            UNIT_STATS[WORKER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)

        min_drone_num = 3  # alternating between first sending an attack force of three drones and then force of two soldiers, then repeating
        myDrone = getAntList(currentState, me, (DRONE,))
        if (food_count >= 2) and (len(myWorker) >= min_worker_num) and (len(myDrone) < min_drone_num):
            if getAntAt(currentState, hill_location) == None:
                return Move(BUILD, [hill_location], DRONE)

        enemny_hill_location = getConstrList(currentState, enemy, (ANTHILL,))[0].coords

        for drone in myDrone:
            if not drone.hasMoved:

                # If enemy has more than 5 food pieces, attack enemy workers
                enemyInv = currentState.inventories[enemy]
                if enemyInv.foodCount >= 5:
                    drone_destination = get_closest_enemy_worker_location(currentState, drone.coords)
                    if drone_destination is not None:
                        path = createPathToward(currentState, drone.coords, drone_destination,
                                                UNIT_STATS[DRONE][MOVEMENT])
                        return Move(MOVE_ANT, path, None)

                # If not, move to enemy ant hill
                temp_path = []
                best_distance = 1000  # Might as well be infinity
                all_paths = listAllMovementPaths(currentState, drone.coords, UNIT_STATS[DRONE][MOVEMENT])
                for path in all_paths:
                    dist = stepsToReach(currentState, path[len(path) - 1], enemny_hill_location)
                    if (dist < best_distance):
                        best_distance = dist
                        temp_path = []
                        temp_path += path

                return Move(MOVE_ANT, temp_path, None)

        mySoldier = getAntList(currentState, me, (SOLDIER,))

        if (food_count >= 2) and (len(myWorker) >= min_worker_num) and (len(myDrone) >= min_drone_num):
            if getAntAt(currentState, hill_location) == None:
                return Move(BUILD, [hill_location], SOLDIER)

        for soldier in mySoldier:
            if not soldier.hasMoved:

                # Move to enemy ant hill
                temp_path = []
                best_distance = 1000  # Might as well be infinity
                all_paths = listAllMovementPaths(currentState, soldier.coords, UNIT_STATS[SOLDIER][MOVEMENT])
                for path in all_paths:
                    dist = stepsToReach(currentState, path[len(path) - 1], enemny_hill_location)
                    if (dist < best_distance):
                        best_distance = dist
                        temp_path = []
                        temp_path += path

                return Move(MOVE_ANT, temp_path, None)

        return Move(END, None, None)

    ##
    # getAttack
    #
    # This agent never attacks
    #
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        return enemyLocations[0]  # don't care

    ##
    # registerWin
    #
    # This agent doesn't learn
    #
    def registerWin(self, hasWon):
        # method template, not implemented
        pass


##
# clearWorkerFromConstructs
#
# finds a valid position for a worker at to go to if they are occupying a construct
# the posiiton returned will be the most optimal step for the worker to take to end up
# at thier future intended destination
#
# Parameters:
#   currentState - current game state
#   construct_coords - the tuple that contains the specified construct's coordinates
#   worker_coords - the tuple that contains the specified workers's coordinates
#   destination_coords - the tuple that contains the specified future destinations's coordinates
#
# Return: a single tuple that represents the coordinates of the most optimal movement location
def clearWorkerFromConstructs(currentState, construct_coords, worker_coords, destination_coords):
    # Move worker if on top of a construct
    if worker_coords == construct_coords:
        temp_coord = []
        temp_dist = 100

        adjacent_places = listAdjacent(worker_coords)
        place_lister = []
        for places in adjacent_places:
            if places in g_construct_coords_except_grass or getAntAt(currentState, places) != None:
                continue
            place_lister.append(places)
            dist = stepsToReach(currentState, places, destination_coords)
            if dist < temp_dist:
                temp_coord = []
                temp_coord.append(places)
                temp_dist = dist
        # print(worker_coords, "Place place_lister", place_lister, " || ", temp_coord)
        if temp_coord:
            return temp_coord[0]
        return None
    else:
        return None


##
# get_closest_enemy_worker_location
#
# finds the closest enemy worker to the specified drone's location
#
# Parameters:
#   currentState - current game state
#   drone_coords - the tuple that contains the specified drone's coordinates
#
# Return: a single tuple that represents the coordinates of the closeset enemy drone
def get_closest_enemy_worker_location(currentState, drone_coords):
    enemy_workers = []
    for yPos in range(6, 10):
        for xPos in range(0, 10):
            getAnt_val = getAntAt(currentState, (xPos, yPos))
            if getAnt_val is not None:
                if getAnt_val.type == 1:
                    enemy_workers.append((xPos, yPos))
    if not enemy_workers:
        return None

    temp_path = []
    best_distance = 1000  # May as well be infinity
    for enemy in enemy_workers:
        dist = stepsToReach(currentState, drone_coords, enemy)
        if dist <= best_distance:
            best_distance = dist
            temp_path = []
            temp_path.append(enemy)

    if temp_path[0]:
        return temp_path[0]
    else:
        return None
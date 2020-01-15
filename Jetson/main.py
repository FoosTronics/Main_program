"""Hoofdclass FoosTronics en main code. 
De onderdelen voor beeldherkenning, AI en motor aansturing komen in dit bestand bijelkaar.
In dit bestand bestaat voor grootendeels uit de regeling van de AI.

File:
    main.py
Date:
    14.1.2020
Version:
    V1.0
Modifier:
    Daniël Boon
Used_IDE:
    Visual Studio Code (Python 3.6.7 64-bit)
""" 
#pylint: disable=E1101

from keeper_sim import keeper_sim
from framework import main
import deep_q_learning_3 as DQL
import matplotlib.pylab as plt
from datetime import datetime
from backends.stepper_controller.P_controller import p_controller
from backends.stepper_controller.src.USBPerformax_multiple_drivers import Commands
import time
from beeld_koppeling import BeeldKoppeling

KEEPER_SPEED = 40

class Foostronics:
    def __init__(self, keeper_sim):
        """initialisatie main.
           bestaat voornamelijk uit AI initialisatie.
        
        Args:
            keeper_sim (class): adress van draaiende keeper simulatie om variabelen op te halen.
        """
        self.ks = keeper_sim
        self.bk = BeeldKoppeling(debug_flag=False)     # class die de beeldherkenning afhandeld. debug_flag=True (trackbars worden afgemaakt).

        self.possible_actions = DQL.create_environment()

        self.stack_size = 4 # We stack 4 frames

        # Initialize deque with zero-images one array for each image
        self.stacked_states = DQL.deque([DQL.np.zeros(4, dtype=DQL.np.float) for i in range(self.stack_size)], maxlen=4) 

                
        ### MODEL HYPERPARAMETERS
        state_size = [4, 4]      # Our input is a stack of 4 frames hence 84x84x4 (Width, height, channels) 
        action_size = 4 #game.get_available_buttons_size()              # 3 possible actions: left, right, shoot
        #TODO: was 0.0002
        learning_rate =  0.01      # Alpha (aka learning rate)

        ### TRAINING HYPERPARAMETERS
        total_episodes = 500        # Total episodes for training
        self.max_steps = 1000              # Max possible steps in an episode
        #TODO: was 64
        self.batch_size = 32

        # Exploration parameters for epsilon greedy strategy
        #TODO: explore_start was 1.0
        self.explore_start = 1.0            # exploration probability at start
        self.explore_stop = 0.01            # minimum exploration probability 
        self.decay_rate = 0.0001            # exponential decay rate for exploration prob

        # Q learning hyperparameters
        self.gamma = 0.95               # Discounting rate

        ### MEMORY HYPERPARAMETERS
        pretrain_length = self.batch_size   # Number of experiences stored in the Memory when initialized for the first time
        memory_size = 10000          # Number of experiences the Memory can keep

        ### MODIFY THIS TO FALSE IF YOU JUST WANT TO SEE THE TRAINED AGENT
        training = True

        ## TURN THIS TO TRUE IF YOU WANT TO RENDER THE ENVIRONMENT
        episode_render = False


        # Reset the graph
        DQL.tf.reset_default_graph()

        # Instantiate the DQNetwork
        self.DQNetwork = DQL.DQNetwork(state_size, action_size, learning_rate)

        
        # Instantiate memory
        self.memory = DQL.Memory(max_size = memory_size)

        # Setup TensorBoard Writer
        self.writer = DQL.tf.summary.FileWriter("/tensorboard/dqn/1")

        ## Losses
        DQL.tf.summary.scalar("Loss", self.DQNetwork.loss)

        self.write_op = DQL.tf.summary.merge_all()

        # Saver will help us to save our model
        self.saver = DQL.tf.train.Saver()

        #with DQL.tf.Session() as self.sess:
        self.sess = DQL.tf.Session()
        # Initialize the variables
        self.sess.run(DQL.tf.global_variables_initializer())
        
        # Initialize the decay rate (that will use to reduce epsilon) 
        self.decay_step = 0
                    # Set step to 0
        self.step = 0
        
        # Initialize the rewards of the episode
        self.episode_rewards = []

        # Make a new episode and observe the first state
        #game.new_episode()
        self.state = DQL.np.array([ks.ball.position.x, ks.ball.position.y, ks.body.position.x, ks.body.position.y])
        
        # Remember that stack frame function also call our preprocess function.
        self.state, self.stacked_states = DQL.stack_states(self.stacked_states, self.state, True, self.stack_size)
        self.goals_old = 0
        self.blocks_old = 0
        self.vel_x_old = 0
        self.vel_y_old = 0
        self.reward = 0
        self.total_reward = []
        self.episode = 0
        self.action = 0

        self.hl, = plt.plot([], [])
        self.points_array = []
        self.met_drivers = False
        try:
            self.pc = p_controller()
            self.met_drivers = True
        except:
            pass
    
    def run(self, ball, keeper, control, target, goals, blocks):
        """Deze functie wordt om iedere frame aangeroepen en kan gezien worden als de mainloop.
        
        Args:
            ball (Box2D object): Box2D object voor ball positie uitlezen
            keeper (Box2D object): Box2D object voor aansturen keeper door AI
            control (class): object voor richtingbepaling van keeper
            target (int): gewenste y positie van keeper om bal tegen te houden
            goals (int): totaal aantal goals
            blocks (int): totaal aantal ballen tegengehouden
        
        Returns:
            ball (Box2D object): update nieuwe ball positie in simulatie
            keeper (Box2D object): update nieuwe keeper aansturing in simulatie
            control (class): update gekozen richting van keeper
            action (int): update gekozen actie van AI in simulatie

        """
        # time.sleep(0.03)
                # wanneer de beeldherkenning aanstaat. Krijg de balpositie.
        if self.ks.shoot_bool:     #voer uit als de beeldherkenning aan hoort.
            ball_pos_old = ball.position
            ball.position = self.bk.getPosVision()
            # * print de cordinaten van de simulatie.
            # print(self.bk.x_s, self.bk.y_s)

        vel_x = 0
        vel_y = 0
        
        for i in range(len(self.state[0])-1):
            vel_x = self.state[0][i+1] - self.state[0][i]
            vel_y = self.state[1][i+1] - self.state[1][i]

        target = self.state[1][0]+(((-15-self.state[0][0])/vel_x) * vel_y)
        
        if(ks.tp):
            ks.DeleteTargetpoint()

        if((vel_x > 0) or (target > 11.26) or (target < 6.16)):
            target = DQL.np.nan
        elif(not DQL.np.isnan(target)):
            ks.CreateTargetpoint((-15, target))

        print(target)

        done = 0
        old_action = self.action

        action, explore_probability = DQL.predict_action(self.explore_start, self.explore_stop, self.decay_rate, self.decay_step, self.state, self.possible_actions, self.sess, self.DQNetwork)
        self.action = action

        if DQL.np.array_equal(action, self.possible_actions[0]):
            control.y = KEEPER_SPEED
            if(self.met_drivers and (not DQL.np.array_equal(action, old_action))):
                self.pc.driver.transceive_message(0, Commands.STOP)
                self.pc.driver.transceive_message(0, Commands.JOG_MIN)
            if(DQL.np.isnan(target)):
                pass
            elif(target > keeper.position.y):
                self.reward += 0.2*abs(keeper.position.y-target)
            else:
                self.reward -= 0.05*(5.1-abs(keeper.position.y-target))
        elif DQL.np.array_equal(action, self.possible_actions[1]):
            control.y = -KEEPER_SPEED
            if(self.met_drivers and (not DQL.np.array_equal(action, old_action))):
                self.pc.driver.transceive_message(0, Commands.STOP)
                self.pc.driver.transceive_message(0, Commands.JOG_PLUS)
            if(DQL.np.isnan(target)):
                pass
            elif(target < keeper.position.y):
                self.reward += 0.2*abs(keeper.position.y-target)
            else:
                self.reward -= 0.05*(5.1-abs(keeper.position.y-target))
        else:
            control.y = 0
            keeper.linearVelocity.y = 0

        if DQL.np.array_equal(action, self.possible_actions[2]):
            old_ball_pos = ball.position
            control.y = 0
            keeper.linearVelocity.y = 0
            
            status = 0
            if(self.met_drivers):
                self.pc.driver.transceive_message(0, Commands.STOP)
                self.pc.shoot()
            elif(1):
                pass
            else:
                control.x = -KEEPER_SPEED
                while(1):
                    # time.sleep(0.03)
                    running = self.checkEvents()
                    self.screen.fill((0, 0, 0))

                    # Check keys that should be checked every loop (not only on initial
                    # keydown)
                    self.CheckKeys()

                    # Run the simulation loop
                    self.SimulationLoop()

                    if GUIEnabled and self.settings.drawMenu:
                        self.gui_app.paint(self.screen)

                    pygame.display.flip()
                    clock.tick(self.settings.c_hz)
                    self.fps = clock.get_fps()

                    self.step += 1
                        
                    # Increase decay_step
                    self.decay_step +=1

                    if((keeper.position.x < -16.59) and (status == 0)):
                        control.x = KEEPER_SPEED
                        status = 1
                    elif((keeper.position.x > -14.41) and (status == 1)):
                        control.x = -KEEPER_SPEED
                        status = 2
                    elif(keeper.position.x < -15 and (status== 2)):
                        control.x = 0
                        keeper.linearVelocity.x = 0
                        break

            if(((ball.position.x - old_ball_pos.x) > 10) and (old_ball_pos.x < -11)):
                self.reward += 0.5
            else:
                self.reward -= 0.1
        
        if DQL.np.array_equal(action, self.possible_actions[3]):
            control.x = 0
            control.y = 0
            keeper.linearVelocity.x = 0
            keeper.linearVelocity.y = 0
            if(self.met_drivers):
                self.pc.driver.transceive_message(0, Commands.STOP)
            if(DQL.np.isnan(target)):
                self.reward += 0.01
            elif(abs(keeper.position.y-target) < 0.37):
                self.reward += 0.3
            else:
                self.reward -= 0.05

        if((ball.position.x < -18) and (ball.position.y < 11.26) and (ball.position.y > 6.16)):
            #self.bk.center
            self.reward += 0
            ks.goals += 1
            self.goals_old = goals
            self.points_array.append(0)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ratio = (100*self.points_array.count(1))/len(self.points_array)
            
            done = 1
        if((self.vel_x_old < 0) and (vel_x > 0) and (ball.position.x < -13) and (ball.position.y < 11.26) and (ball.position.y > 6.16)):#ball.position):
            self.reward += 1
            self.blocks_old += 1
            self.points_array.append(1)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ratio = (100*self.points_array.count(1))/len(self.points_array)
            done = 1  

        self.vel_x_old = vel_x
        

        # Add the reward to total reward
        self.episode_rewards.append(self.reward)
        
        
        # If the game is finished
        if done:
            #self.bk.resetCoordinates()
            if(self.met_drivers):
                self.pc.driver.transceive_message(0, Commands.STOP)
                if(keeper.position.y >=8.71):
                    self.pc.go_home()
                else:
                    self.pc.go_home(1)
            # the episode ends so no next state
            next_state = DQL.np.zeros((4), dtype=DQL.np.float)
            next_state, self.stacked_states = DQL.stack_states(self.stacked_states, next_state, False, self.stack_size)

            # Set step = max_steps to end the episode
            self.step = self.max_steps

            # Get the total reward of the episode
            self.total_reward.append(DQL.np.sum(self.episode_rewards))

            self.hl.set_xdata(DQL.np.append(self.hl.get_xdata(), (len(self.total_reward)-1)))
            self.hl.set_ydata(DQL.np.append(self.hl.get_ydata(), DQL.np.sum(self.episode_rewards)))                    
            plt.axis([0, len(self.total_reward), min(self.total_reward), max(self.total_reward)])
            plt.draw()
            plt.pause(0.0001)
            plt.show

            self.episode_rewards = []
            done = 0
            if self.episode % 500 == 0:
                date_time = datetime.now().strftime("%m-%d-%Y,%H-%M-%S")
                save_path = self.saver.save(self.sess, "AI_models/AI_save_%s_episode_%d.ckpt" % (date_time, self.episode))
                print("AI model saved")
            self.episode += 1

            self.memory.add((self.state, action, self.reward, next_state, done))

        else:
            # Get the next state
            next_state =  DQL.np.array([ball.position.x, ball.position.y, keeper.position.x, keeper.position.y])
            
            # Stack the frame of the next_state
            next_state, self.stacked_states = DQL.stack_states(self.stacked_states, next_state, False, self.stack_size)
            

            # Add experience to memory
            self.memory.add((self.state, action, self.reward, next_state, done))
            
            # st+1 is now our current state
            self.state = next_state


        ### LEARNING PART            
        # Obtain random mini-batch from memory
        batch = self.memory.sample(self.batch_size)
        states_mb = DQL.np.array([each[0] for each in batch], ndmin=3)
        actions_mb = DQL.np.array([each[1] for each in batch])
        rewards_mb = DQL.np.array([each[2] for each in batch]) 
        next_states_mb = DQL.np.array([each[3] for each in batch], ndmin=3)
        dones_mb = DQL.np.array([each[4] for each in batch])

        target_Qs_batch = []

            # Get Q values for next_state 
        Qs_next_state = self.sess.run(self.DQNetwork.output, feed_dict = {self.DQNetwork.inputs_: next_states_mb})
        
        # Set Q_target = r if the episode ends at s+1, otherwise set Q_target = r + gamma*maxQ(s', a')
        for i in range(0, len(batch)):
            terminal = dones_mb[i]

            # If we are in a terminal state, only equals reward
            if terminal:
                target_Qs_batch.append(rewards_mb[i])
                
            else:
                target_ai = rewards_mb[i] + self.gamma * DQL.np.max(Qs_next_state[i])
                target_Qs_batch.append(target_ai)
                

        targets_mb = DQL.np.array([each for each in target_Qs_batch])

        loss, _ = self.sess.run([self.DQNetwork.loss, self.DQNetwork.optimizer],
                            feed_dict={self.DQNetwork.inputs_: states_mb,
                                        self.DQNetwork.target_Q: targets_mb,
                                        self.DQNetwork.actions_: actions_mb})

        # Write TF Summaries
        summary = self.sess.run(self.write_op, feed_dict={self.DQNetwork.inputs_: states_mb,
                                            self.DQNetwork.target_Q: targets_mb,
                                            self.DQNetwork.actions_: actions_mb})
        self.writer.add_summary(summary,1)
        self.writer.flush()
        self.reward = 0

        return ball, keeper, control, action



if __name__ == "__main__":
    """start main code
    """
    ks = keeper_sim()
    ks.set_Foostronics(Foostronics)
    main(ks)
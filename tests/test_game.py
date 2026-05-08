import random
import unittest

from lazy_bob.game import (
    BOB_SPRITES,
    JUMP_EXCLAMATIONS_CASUAL,
    JUMP_EXCLAMATIONS_FAST,
    Obstacle,
    create_state,
    current_bob_sprite,
    detect_collision,
    jump,
    step,
)


class LazyBobTests(unittest.TestCase):
    def test_jump_only_when_grounded(self) -> None:
        state = create_state(48, 16, best_score=0)
        jump(state)
        self.assertLess(state.bob_velocity, 0)

        airborne = create_state(48, 16, best_score=0)
        airborne.bob_y -= 2
        jump(airborne)
        self.assertEqual(airborne.bob_velocity, 0)

    def test_collision_detected_on_ground(self) -> None:
        state = create_state(48, 16, best_score=0)
        state.obstacles.append(Obstacle(x=float(state.bob_x)))
        self.assertTrue(detect_collision(state))

    def test_collision_detected_when_obstacle_skips_past_bob(self) -> None:
        state = create_state(48, 16, best_score=0)
        state.obstacles.append(
            Obstacle(x=float(state.bob_x) - 1.2, previous_x=float(state.bob_x) + 1.4)
        )
        self.assertTrue(detect_collision(state))

    def test_step_awards_score_after_passing(self) -> None:
        state = create_state(48, 16, best_score=0)
        state.obstacles.append(Obstacle(x=float(state.bob_x) - 0.1))
        step(state, random.Random(1))
        self.assertEqual(state.score, 1)
        self.assertEqual(state.best_score, 1)

    def test_jump_switches_bob_into_air_pose(self) -> None:
        state = create_state(48, 16, best_score=0)
        jump(state, random.Random(1))
        step(state, random.Random(1))
        self.assertEqual(current_bob_sprite(state), BOB_SPRITES["jump"])

    def test_wide_obstacle_counts_for_collision(self) -> None:
        state = create_state(48, 16, best_score=0)
        state.obstacles.append(Obstacle(x=float(state.bob_x + 1), shape=["[]"]))
        self.assertTrue(detect_collision(state))

    def test_jump_sets_a_lazy_exclamation(self) -> None:
        state = create_state(48, 16, best_score=0)
        jump(state, random.Random(1))
        self.assertTrue(state.jump_exclamation)
        self.assertGreater(state.jump_exclamation_ticks, 0)
        self.assertTrue(state.bobism)
        self.assertGreater(state.bobism_ticks, 0)

    def test_fast_jump_uses_faster_exclamation_pool(self) -> None:
        state = create_state(48, 16, best_score=0)
        state.speed = 2.2
        jump(state, random.Random(1))
        self.assertIn(state.jump_exclamation, JUMP_EXCLAMATIONS_FAST)

    def test_scoring_can_trigger_bobism(self) -> None:
        state = create_state(48, 16, best_score=0)
        state.score = 4
        state.obstacles.append(Obstacle(x=float(state.bob_x) - 0.1))
        step(state, random.Random(1))
        self.assertEqual(state.score, 5)
        self.assertTrue(state.bobism)


if __name__ == "__main__":
    unittest.main()

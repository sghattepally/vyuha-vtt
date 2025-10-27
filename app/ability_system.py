# app/ability_system.py
"""
Core Ability System for Vyuha VTT
Handles validation, targeting, effects, and execution of all abilities.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from . import models
from pydantic import BaseModel
import math
import random
from . import loka_system

# ==================================
# Pydantic Schemas for Type Safety
# ==================================

class TargetInfo(BaseModel):
    """Represents a single target (participant or position)"""
    participant_id: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None

class AbilityExecutionRequest(BaseModel):
    """Request to execute an ability"""
    actor_id: int
    ability_id: int
    primary_target: TargetInfo
    secondary_targets: List[TargetInfo] = []

class AbilityExecutionResult(BaseModel):
    """Result of ability execution"""
    success: bool
    message: str
    log_events: List[Dict[str, Any]] = []
    affected_participants: List[int] = []

# ==================================
# Helper Functions
# ==================================

def get_modifier(score: int) -> int:
    """Calculate D&D-style modifier from attribute score"""
    return (score - 10) // 2

def calculate_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate grid distance (Chebyshev distance for 8-directional movement)"""
    return max(abs(x1 - x2), abs(y1 - y2))

def get_participants_in_radius(
    db: Session, 
    session_id: int, 
    center_x: int, 
    center_y: int, 
    radius: int
) -> List[models.SessionCharacter]:
    """Get all participants within a given radius of a point"""
    all_participants = db.query(models.SessionCharacter).filter(
        models.SessionCharacter.session_id == session_id,
        models.SessionCharacter.x_pos.isnot(None)
    ).all()
    
    return [
        p for p in all_participants 
        if calculate_distance(p.x_pos, p.y_pos, center_x, center_y) <= radius
    ]

# ==================================
# Core Ability System Class
# ==================================

class AbilitySystem:
    """
    Central system for ability resolution.
    Handles validation, targeting, resource management, and effect application.
    """
    
    def __init__(self, db: Session, session_id: int):
        self.db = db
        self.session_id = session_id
        self.session = db.query(models.GameSession).filter(
            models.GameSession.id == session_id
        ).first()
    
    # ==================================
    # Validation Methods
    # ==================================
    def _get_active_resonance(self, character: models.Character) -> Tuple[str, bool]:
        """
        Get the active resonance affecting this character.
        Returns (resonance_type, is_enhanced)
        """
        # Check for active summoning (overrides environmental)
        if (self.session.active_loka_summoning and 
            self.session.active_loka_summoning.get("turns_remaining", 0) > 0):
            resonance = self.session.active_loka_summoning["type"]
            is_enhanced = self.session.active_loka_summoning.get("is_enhanced", False)
        else:
            # Fall back to environmental resonance
            resonance = self.session.environmental_resonance or "none"
            is_enhanced = False
        
        # Characters with Loka Resistance ignore all resonance
        if character.has_loka_resistance:
            return "none", False
        
        return resonance, is_enhanced


    def validate_ability_use(
        self, 
        actor: models.SessionCharacter, 
        ability: models.Ability
    ) -> Tuple[bool, str]:
        """
        Validates whether an actor can use an ability.
        Returns (is_valid, error_message)
        """
        # Check if actor is downed
        if actor.status == "downed":
            return False, f"{actor.character.name} is downed and cannot act."
        # Check action economy
        if ability.action_type == models.ActionType.ACTION and actor.actions < 1:
            return False, "No actions remaining this turn."
        elif ability.action_type == models.ActionType.BONUS_ACTION and actor.bonus_actions < 1:
            return False, "No bonus actions remaining this turn."
        elif ability.action_type == models.ActionType.REACTION and actor.reactions < 1:
            return False, "No reactions remaining this turn."
        elif ability.action_type == models.ActionType.FREE:
            if ability.resource_type == models.ResourceType.SPEED:
                if actor.remaining_speed < ability.resource_cost:
                    return False, f"Insufficient movement (need {ability.resource_cost}, have {actor.remaining_speed})."
        
        # Check resource costs
        active_resonance, is_enhanced = self._get_active_resonance(actor.character)
        has_loka_resistance = actor.character.has_loka_resistance
    
        if ability.resource_type == models.ResourceType.TAPAS:
        # Calculate modified cost
            modified_cost = loka_system.apply_resonance_to_ability_cost(
                base_cost=ability.resource_cost,
                ability_resource="tapas",
                active_resonance=active_resonance,
                is_enhanced=is_enhanced,
                has_loka_resistance=has_loka_resistance
            )
        
        if actor.current_tapas < modified_cost:
            return False, f"Insufficient Tapas (need {modified_cost}, have {actor.current_tapas})."
    
        elif ability.resource_type == models.ResourceType.MAYA:
        # Calculate modified cost
            modified_cost = loka_system.apply_resonance_to_ability_cost(
                base_cost=ability.resource_cost,
                ability_resource="maya",
                active_resonance=active_resonance,
                is_enhanced=is_enhanced,
                has_loka_resistance=has_loka_resistance
        )
        
        if actor.current_maya < modified_cost:
            return False, f"Insufficient Māyā (need {modified_cost}, have {actor.current_maya})."
    
        elif ability.resource_type == models.ResourceType.SPEED:
        # Movement doesn't use resonance
            if actor.remaining_speed < 1:
                return False, f"No movement speed remaining this turn."
    
        # Check custom requirements (JSON-based)
        if ability.requirements:
            is_valid, msg = self._check_custom_requirements(actor, ability.requirements)
            if not is_valid:
                return False, msg
        
        print("DEBUG_VALIDATE: PASSED validate_ability_use.")
        return True, ""
    
    def _check_custom_requirements(
        self, 
        actor: models.SessionCharacter, 
        requirements: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check JSON-defined custom requirements"""
        
        # Example: {"equipped_weapon_type": "weapon"}
        if "equipped_weapon_type" in requirements:
            required_type = requirements["equipped_weapon_type"]
            # Query actor's equipped items
            equipped = self.db.query(models.CharacterInventory).filter(
                models.CharacterInventory.character_id == actor.character_id,
                models.CharacterInventory.is_equipped == True
            ).all()
            
            has_required = any(
                inv.item.item_type.value == required_type 
                for inv in equipped
            )
            if not has_required:
                return False, f"Requires a {required_type} to be equipped."
        
        # Example: {"min_prajna": 14}
        if "min_prajna" in requirements:
            from .main import CharacterSchema  # Import to calculate attributes
            char_schema = CharacterSchema.model_validate(actor.character)
            if char_schema.prajna < requirements["min_prajna"]:
                return False, f"Requires Prajñā {requirements['min_prajna']} or higher."
        
        # Add more requirement types as needed
        
        return True, ""
    
    def validate_targeting(
        self, 
        actor: models.SessionCharacter, 
        ability: models.Ability,
        target_info: TargetInfo
    ) -> Tuple[bool, str, Optional[models.SessionCharacter]]:
        """
        Validates targeting for an ability.
        Returns (is_valid, error_message, target_participant_or_None)
        """
        
        # Handle SELF targeting
        if ability.target_type == models.TargetType.SELF:
            return True, "", actor
        
        # Handle GROUND targeting
        if ability.target_type == models.TargetType.GROUND:
            if target_info.x is None or target_info.y is None:
                print(f"DEBUG: Validation FAIL - GROUND target missing coords: {target_info}")
                return False, "Ground target requires x, y coordinates.", None
            
            # Check range to target position
            distance = calculate_distance(
                actor.x_pos, actor.y_pos, 
                target_info.x, target_info.y
            )
            if distance > ability.range:
                return False, f"Target location is out of range (max {ability.range}).", None
            
            return True, "", None
        
        # Handle ENEMY/ALLY targeting
        if target_info.participant_id is None:
            return False, "Must specify a target participant.", None
        
        target = self.db.query(models.SessionCharacter).filter(
            models.SessionCharacter.id == target_info.participant_id,
            models.SessionCharacter.session_id == self.session_id
        ).first()
        
        if not target:
            return False, "Invalid target.", None
        
        # Check if target is on grid
        if target.x_pos is None or actor.x_pos is None:
            return False, "Actor or target not on grid.", None
        
        # Check range
        distance = calculate_distance(
            actor.x_pos, actor.y_pos, 
            target.x_pos, target.y_pos
        )
        if distance > ability.range:
            return False, f"Target is out of range (max {ability.range}).", None
        
        # Check ally/enemy targeting
        is_ally = (target.player_id == actor.player_id)
        
        if ability.target_type == models.TargetType.ALLY and not is_ally:
            return False, "Can only target allies.", None
        elif ability.target_type == models.TargetType.ENEMY and is_ally:
            return False, "Can only target enemies.", None
        
        return True, "", target
    
    # ==================================
    # Resource Management
    # ==================================
    
    def consume_resources(
        self, 
        actor: models.SessionCharacter, 
        ability: models.Ability
    ):
        """Deduct resources and action economy"""
        
        # Consume action economy
        if ability.action_type == models.ActionType.ACTION:
            actor.actions -= 1
        elif ability.action_type == models.ActionType.BONUS_ACTION:
            actor.bonus_actions -= 1
        elif ability.action_type == models.ActionType.REACTION:
            actor.reactions -= 1
        
        # Consume resources
        active_resonance, is_enhanced = self._get_active_resonance(actor.character)
        has_loka_resistance = actor.character.has_loka_resistance
    
        if ability.resource_type == models.ResourceType.TAPAS:
            modified_cost = loka_system.apply_resonance_to_ability_cost(
            base_cost=ability.resource_cost,
            ability_resource="tapas",
            active_resonance=active_resonance,
            is_enhanced=is_enhanced,
            has_loka_resistance=has_loka_resistance
        )
            actor.current_tapas -= modified_cost
        
        elif ability.resource_type == models.ResourceType.MAYA:
            modified_cost = loka_system.apply_resonance_to_ability_cost(
            base_cost=ability.resource_cost,
            ability_resource="maya",
            active_resonance=active_resonance,
            is_enhanced=is_enhanced,
            has_loka_resistance=has_loka_resistance
        )
            actor.current_maya -= modified_cost
        
        elif ability.resource_type == models.ResourceType.SPEED:
            actor.remaining_speed -= ability.resource_cost
        
        elif ability.resource_type == models.ResourceType.PRANA:
            actor.current_prana = max(0, actor.current_prana - ability.resource_cost)
    
        self.db.add(actor)
    
    # ==================================
    # Effect Application
    # ==================================
    
    def apply_damage_effect(
        self, 
        actor: models.SessionCharacter,
        target: models.SessionCharacter,
        ability: models.Ability
    ) -> Dict[str, Any]:
        """
        Applies a damage effect with attack roll.
        Returns log details.
        """
        from .main import CharacterSchema
        
        actor_char = CharacterSchema.model_validate(actor.character)
        target_char = CharacterSchema.model_validate(target.character)
        
        active_resonance, is_enhanced = self._get_active_resonance(actor.character)
        has_loka_resistance = actor.character.has_loka_resistance
    
        # Determine if this is a Tapas or Maya ability based on its cost
        if ability.resource_type == models.ResourceType.TAPAS:
            ability_resource = "tapas"
        elif ability.resource_type == models.ResourceType.MAYA:
            ability_resource = "maya"
        else:
            ability_resource = None
    
        # Apply resonance modifier to the to-hit modifier
        if ability_resource:
            resonance_mod = loka_system.apply_resonance_to_ability_roll(
                base_roll=0,  # We're modifying the modifier, not the d20 roll itself
                ability_resource=ability_resource,
                active_resonance=active_resonance,
                is_enhanced=is_enhanced,
                has_loka_resistance=has_loka_resistance
            )
            to_hit_mod += resonance_mod


        attack_roll = random.randint(1, 20)
        total_attack = attack_roll + to_hit_mod
        
        # Evasion DC
        evasion_dc = 10 + get_modifier(target_char.dakshata)
        
        # Hit or Miss
        if total_attack >= evasion_dc:
            # Calculate damage
            damage_mod = 0
            if ability.damage_attribute:
                damage_mod = get_modifier(getattr(actor_char, ability.damage_attribute))
            
            num, dice = map(int, ability.damage_dice.split('d'))
            damage_roll = sum(random.randint(1, dice) for _ in range(num))
            total_damage = max(0, damage_roll + damage_mod)
            
            # Apply damage
            target.current_prana = max(0, target.current_prana - total_damage)
            self.db.add(target)
            
            # Check if downed
            if target.current_prana == 0:
                target.status = "downed"
                self.db.add(target)
            
            return {
                "event_type": "attack_hit",
                "actor_name": actor.character.name,
                "target_name": target.character.name,
                "ability_name": ability.name,
                "roll": attack_roll,
                "modifier": to_hit_mod,
                "total": total_attack,
                "dc": evasion_dc,
                "damage": total_damage
            }
        else:
            return {
                "event_type": "attack_miss",
                "actor_name": actor.character.name,
                "target_name": target.character.name,
                "ability_name": ability.name,
                "roll": attack_roll,
                "modifier": to_hit_mod,
                "total": total_attack,
                "dc": evasion_dc
            }
    
    def apply_healing_effect(
        self,
        actor: models.SessionCharacter,
        target: models.SessionCharacter,
        ability: models.Ability
    ) -> Dict[str, Any]:
        """Applies a healing effect"""
        from .main import CharacterSchema
        print(f"DEBUG_HEAL: Applying heal effect from {ability.name} to {target.character.name}")
        print(f"DEBUG_HEAL: Target's Prana BEFORE heal: {target.current_prana}")
        target_char = CharacterSchema.model_validate(target.character)
        
        # Calculate healing
        num, dice = map(int, ability.damage_dice.split('d'))  # Reuse damage_dice for healing
        healing_roll = sum(random.randint(1, dice) for _ in range(num))
        
        # Add modifier if applicable
        healing_mod = 0
        if ability.damage_attribute:
            actor_char = CharacterSchema.model_validate(actor.character)
            healing_mod = get_modifier(getattr(actor_char, ability.damage_attribute))
        
        total_healing = healing_roll + healing_mod
        
        # Apply healing
        old_prana = target.current_prana
        target.current_prana = min(target.current_prana + total_healing, target_char.max_prana)
        actual_healing = target.current_prana - old_prana
        self.db.add(target)
        
        return {
            "event_type": "heal",
            "actor_name": actor.character.name,
            "target_name": target.character.name,
            "ability_name": ability.name,
            "healing": actual_healing
        }
    
    def apply_teleport_effect(
        self,
        actor: models.SessionCharacter,
        target_pos: TargetInfo,
        ability: models.Ability
    ) -> Dict[str, Any]:
        """
        Applies a teleport (movement) effect to the actor.
        """
        if target_pos.x is None or target_pos.y is None:
            return {
                "event_type": "error",
                "message": "Teleport ability failed: No target position provided."
            }
            
        old_pos = {"x": actor.x_pos, "y": actor.y_pos}
        distance_moved = calculate_distance(
            actor.x_pos, actor.y_pos, 
            target_pos.x, target_pos.y
        )
        if ability.resource_type == models.ResourceType.SPEED:
            if distance_moved > actor.remaining_speed:
                return {
                    "event_type": "error",
                    "message": f"Teleport failed: Not enough speed to move {distance_moved} units."
                }
            actor.remaining_speed -= distance_moved
        # 1. Update the actor's position
        actor.x_pos = target_pos.x
        actor.y_pos = target_pos.y
        self.db.add(actor)
        
        # 2. Add Status Effect if specified (e.g., 'invisible_until_next_turn' for Shadow Step)
        if ability.status_effect:
            actor.status = ability.status_effect
            self.db.add(actor)
        
        # 3. Return log details
        return {
            "event_type": "teleport",
            "actor_name": actor.character.name,
            "ability_name": ability.name,
            "old_pos": old_pos,
            "new_pos": {"x": actor.x_pos, "y": actor.y_pos},
            "status_applied": ability.status_effect
        }
    
    # ==================================
    # Main Execution Method
    # ==================================
    
    def execute_ability(
        self, 
        request: AbilityExecutionRequest
    ) -> AbilityExecutionResult:
        """
        Main entry point for ability execution.
        Orchestrates the entire resolution pipeline.
        """
        print(f"DEBUG: Executing ability {request.ability_id} by actor {request.actor_id}.")
        print(f"DEBUG: Primary target received: {request.primary_target.model_dump()}")
        # 1. Load actor and ability
        actor = self.db.query(models.SessionCharacter).filter(
            models.SessionCharacter.id == request.actor_id
        ).first()
        
        ability = self.db.query(models.Ability).filter(
            models.Ability.id == request.ability_id
        ).first()
        
        if not actor or not ability:
            return AbilityExecutionResult(
                success=False,
                message="Invalid actor or ability."
            )
        
        # 2. Validate ability use
        is_valid, error_msg = self.validate_ability_use(actor, ability)
        if not is_valid:
            return AbilityExecutionResult(success=False, message=error_msg)
        
        # 3. Validate targeting
        is_valid, error_msg, primary_target = self.validate_targeting(
            actor, ability, request.primary_target
        )
        if not is_valid:
            return AbilityExecutionResult(success=False, message=error_msg)
        
        # 4. Consume resources
        if not (ability.effect_type == "teleport" and ability.resource_type == models.ResourceType.SPEED):
            self.consume_resources(actor, ability)
        
        # 5. Determine affected participants
        affected = []
        log_events = []
        
        if ability.target_type == models.TargetType.SELF:
            print("DEBUG: Validation PASSED for SELF target.")
            affected = [actor]
        
        if ability.effect_type == "teleport":
                # Only the actor is affected, and the target is the position
                log_detail = self.apply_teleport_effect(
                    actor, 
                    request.primary_target, # Target position is here for GROUND
                    ability
                )
                log_events.append(log_detail)
                
                return AbilityExecutionResult(
                    success=True,
                    message=f"{actor.character.name} used {ability.name} and moved!",
                    log_events=log_events,
                    affected_participants=[actor.id]
                )

        elif ability.target_type == models.TargetType.GROUND:
            # Area of effect
            affected = get_participants_in_radius(
                self.db, self.session_id,
                request.primary_target.x, request.primary_target.y,
                ability.effect_radius
            )
        
        elif ability.target_type in [models.TargetType.ENEMY, models.TargetType.ALLY]:
            # Single target or area around target
            if ability.effect_radius > 0:
                affected = get_participants_in_radius(
                    self.db, self.session_id,
                    primary_target.x_pos, primary_target.y_pos,
                    ability.effect_radius
                )
            else:
                affected = [primary_target]
        
        # 6. Apply effects to all affected participants
        for target in affected:
            if ability.effect_type == "damage":
                log_detail = self.apply_damage_effect(actor, target, ability)
                log_events.append(log_detail)
            
            elif ability.effect_type == "heal":
                log_detail = self.apply_healing_effect(actor, target, ability)
                log_events.append(log_detail)
            
            # Add more effect types here (buff, debuff, teleport, etc.)
        
        # 7. Commit changes
        self.db.commit()
        
        return AbilityExecutionResult(
            success=True,
            message=f"{actor.character.name} used {ability.name}!",
            log_events=log_events,
            affected_participants=[p.id for p in affected]
        )
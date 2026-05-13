// Define Asides state
class Asides {
  leftOpen = $state(true);
  rightOpen = $state(true);
  prevLeftOpen = $state(true);
  prevRightOpen = $state(true);

  leftToggle(state?: boolean) {
    if (state === undefined) {
      this.leftOpen = !this.leftOpen;
      return;
    }
    this.leftOpen = state;
  }

  rightToggle(state?: boolean) {
    if (state === undefined) {
      this.rightOpen = !this.rightOpen;
      return;
    }
    this.rightOpen = state;
  }

  saveState() {
    this.prevLeftOpen = this.leftOpen;
    this.prevRightOpen = this.rightOpen;
  }

  restore() {
    this.leftOpen = this.prevLeftOpen;
    this.rightOpen = this.prevRightOpen;
  }

  hideLeft() {
    this.leftOpen = false;
  }

  hideRight() {
    this.rightOpen = false;
  }

  hideAll() {
    this.saveState();
    this.leftOpen = false;
    this.rightOpen = false;
  }

  reset() {
    this.leftOpen = false;
    this.rightOpen = false;
    this.prevLeftOpen = false;
    this.prevRightOpen = false;
  }
}
export const asides = new Asides();